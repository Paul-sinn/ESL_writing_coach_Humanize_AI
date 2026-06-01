from __future__ import annotations

import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from sqlalchemy import select

from .config import get_settings
from .db.database import DbSession
from .db.models import Profile, UserActivityLogDB
from .graphs import calculate_coach_credits, calculate_humanize_credits, coach_graph, humanize_graph
from .schemas import (
    BillingStatusResponse,
    CheckoutRequest,
    CheckoutResponse,
    CoachRequest,
    CoachResponse,
    CompleteOnboardingRequest,
    CompleteOnboardingResponse,
    DeleteAccountResponse,
    DemoLoginRequest,
    DemoLoginResponse,
    HumanizeRequest,
    HumanizeResponse,
    UserResponse,
    USERNAME_PATTERN,
)
from .services import auth as auth_service
from .services.billing import (
    PolarCheckoutConfigError,
    PolarCheckoutUpstreamError,
    billing_service,
    is_recurring_product_code,
)
from .lib.encryption import decrypt
from .services.polar_webhook import (
    handle_order_event,
    handle_subscription_event,
    verify_webhook_signature,
)
from .utils.text import count_words


settings = get_settings()


def _uses_persistent_billing(user_id: str) -> bool:
    try:
        UUID(user_id)
    except ValueError:
        return False
    return True


def _billing_limit_detail(response: CoachResponse | HumanizeResponse) -> dict | None:
    redirect = response.billing_redirect
    if redirect is None:
        return None
    return {
        "message": redirect.message,
        "recommended_offer": redirect.recommended_offer,
        "upgrade_url": redirect.route,
        "checkout_options": [option.model_dump() for option in redirect.checkout_options],
    }


def _maybe_decrypt(value: str | None) -> str | None:
    if value and value.count(":") == 2:
        return decrypt(value)
    return value


async def _load_profile(user_id: str, db) -> Profile | None:
    result = await db.execute(select(Profile).where(Profile.id == user_id))
    return result.scalar_one_or_none()


async def _require_active_user(current_user, db: DbSession) -> Profile | None:
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    user_id = current_user.user_id
    if not _uses_persistent_billing(user_id):
        return None
    if db is None:
        raise HTTPException(status_code=503, detail="Account database is unavailable.")
    profile = await _load_profile(user_id, db)
    if profile is not None and profile.deleted_at is not None:
        raise HTTPException(status_code=403, detail="This account has been deleted.")
    return profile


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from .db.init_db import create_tables, should_bootstrap_schema
        await create_tables()
        if should_bootstrap_schema():
            print("✅ DB tables created / verified.")
        else:
            print("✅ DB connection verified; remote schema bootstrap skipped.")
    except Exception as e:
        print(f"⚠️  DB startup failed: {e}")
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _reserve_credits(user_id: str, amount: int, feature: str, db) -> int | None:
    if db is None or amount <= 0:
        return None
    try:
        ledger_id = await billing_service.async_reserve_credits(user_id, amount, feature, db)
        await db.commit()
        return ledger_id
    except ValueError:
        await db.rollback()
        return None


@app.post("/api/coach", response_model=CoachResponse)
async def coach(
    payload: CoachRequest,
    db: DbSession,
    current_user=Depends(auth_service.get_current_user),
) -> CoachResponse:
    await _require_active_user(current_user, db)
    user_id = current_user.user_id
    reserved_ledger_id: int | None = None

    if db is not None and _uses_persistent_billing(user_id):
        await billing_service.async_load_to_memory(user_id, db)
        status = billing_service.get_status(user_id)
        if status.subscription_status != "free":
            credits_required = calculate_coach_credits(count_words(payload.text), payload.depth)
            reserved_ledger_id = await _reserve_credits(user_id, credits_required, "coach", db)

    try:
        result = coach_graph.invoke({
            "user_id": user_id,
            "text": payload.text,
            "assignment_type": payload.assignment_type,
            "writing_level": payload.writing_level,
            "depth": payload.depth,
            "credits_reserved": reserved_ledger_id is not None,
        })
        response = result["response"]
        if reserved_ledger_id is not None and db is not None:
            if response.billing_redirect or response.credits_charged <= 0:
                await billing_service.async_release_reservation(reserved_ledger_id, db)
            else:
                await billing_service.async_capture_reservation(reserved_ledger_id, db)
                await billing_service.async_record_usage(
                    user_id,
                    feature="coach",
                    words=response.input_word_count,
                    credits_used=response.credits_charged,
                    db=db,
                )
            await db.commit()
        elif db is not None and _uses_persistent_billing(user_id) and not response.billing_redirect:
            await billing_service.async_record_usage(
                user_id,
                feature="coach",
                words=response.input_word_count,
                credits_used=response.credits_charged,
                db=db,
            )
            await db.commit()
    except Exception:
        if reserved_ledger_id is not None and db is not None:
            await billing_service.async_release_reservation(reserved_ledger_id, db)
            await db.commit()
        raise

    limit_detail = _billing_limit_detail(response)
    if limit_detail is not None:
        raise HTTPException(status_code=429, detail=limit_detail)
    return response


@app.post("/api/humanize", response_model=HumanizeResponse)
async def humanize(
    payload: HumanizeRequest,
    db: DbSession,
    current_user=Depends(auth_service.get_current_user),
) -> HumanizeResponse:
    await _require_active_user(current_user, db)
    user_id = current_user.user_id
    reserved_ledger_id: int | None = None

    if db is not None and _uses_persistent_billing(user_id):
        await billing_service.async_load_to_memory(user_id, db)
        status = billing_service.get_status(user_id)
        if status.subscription_status != "free":
            credits_required = calculate_humanize_credits(count_words(payload.text))
            reserved_ledger_id = await _reserve_credits(user_id, credits_required, "humanize", db)

    try:
        result = humanize_graph.invoke({
            "user_id": user_id,
            "text": payload.text,
            "tone": payload.tone,
            "strength": payload.strength,
            "persona": payload.persona,
            "coach_feedback": payload.coach_feedback,
            "preserve_meaning": payload.preserve_meaning,
            "preserve_citations": payload.preserve_citations,
            "preserve_structure": payload.preserve_structure,
            "credits_reserved": reserved_ledger_id is not None,
        })
        response = result["response"]
        if reserved_ledger_id is not None and db is not None:
            if response.billing_redirect or response.credits_charged <= 0:
                await billing_service.async_release_reservation(reserved_ledger_id, db)
            else:
                await billing_service.async_capture_reservation(reserved_ledger_id, db)
                await billing_service.async_record_usage(
                    user_id,
                    feature="humanize",
                    words=response.input_word_count,
                    credits_used=response.credits_charged,
                    db=db,
                )
            await db.commit()
        elif db is not None and _uses_persistent_billing(user_id) and not response.billing_redirect:
            await billing_service.async_record_usage(
                user_id,
                feature="humanize",
                words=response.input_word_count,
                credits_used=response.credits_charged,
                db=db,
            )
            await db.commit()
    except Exception:
        if reserved_ledger_id is not None and db is not None:
            await billing_service.async_release_reservation(reserved_ledger_id, db)
            await db.commit()
        raise

    limit_detail = _billing_limit_detail(response)
    if limit_detail is not None:
        raise HTTPException(status_code=429, detail=limit_detail)
    return response


@app.get("/api/billing/status", response_model=BillingStatusResponse)
async def billing_status(
    db: DbSession,
    current_user=Depends(auth_service.get_current_user),
) -> BillingStatusResponse:
    await _require_active_user(current_user, db)
    user_id = current_user.user_id
    if db is not None and _uses_persistent_billing(user_id):
        try:
            synced = await billing_service.async_sync_from_polar_customer_state(user_id, db)
            if synced:
                await db.commit()
            await billing_service.async_load_to_memory(user_id, db)
        except Exception:
            pass
    return billing_service.get_status(user_id)


@app.get("/api/auth/check-username")
async def check_username(username: str, db: DbSession) -> dict:
    username = username.strip()
    if not USERNAME_PATTERN.fullmatch(username):
        return {"available": False}
    if db is None:
        return {"available": True}
    try:
        result = await db.execute(select(Profile).where(Profile.username == username))
        return {"available": result.scalar_one_or_none() is None}
    except Exception:
        return {"available": True}


@app.get("/api/auth/check-nickname")
async def check_nickname(nickname: str, db: DbSession) -> dict:
    if db is None:
        return {"available": True}
    try:
        result = await db.execute(select(Profile).where(Profile.nickname == nickname))
        return {"available": result.scalar_one_or_none() is None}
    except Exception:
        return {"available": True}


@app.post("/api/auth/demo-login", response_model=DemoLoginResponse)
async def demo_login(payload: DemoLoginRequest) -> DemoLoginResponse:
    if not auth_service.verify_demo_credentials(payload.email, payload.password):
        raise HTTPException(status_code=401, detail="Invalid demo credentials.")
    return DemoLoginResponse(
        access_token=auth_service.create_demo_access_token(payload.email),
        email=payload.email,
        user_id=settings.demo_login_user_id,
        username="demo",
        nickname="Demo Student",
    )


@app.get("/api/auth/me", response_model=UserResponse)
async def auth_me(
    db: DbSession,
    current_user=Depends(auth_service.get_current_user),
) -> UserResponse:
    profile = await _require_active_user(current_user, db)
    user_id = current_user.user_id
    if db is not None and _uses_persistent_billing(user_id):
        try:
            await billing_service.async_load_to_memory(user_id, db)
        except Exception:
            pass
    status = billing_service.get_status(user_id)
    profile_name = None
    needs_onboarding = False
    if profile:
        profile_name = _maybe_decrypt(getattr(profile, "full_name", None)) or profile.nickname
        needs_onboarding = not (
            profile.username
            and profile.terms_accepted_at
            and profile.privacy_accepted_at
        )
    elif _uses_persistent_billing(user_id):
        needs_onboarding = True
    return UserResponse(
        email=current_user.email,
        username=profile.username if profile else None,  # type: ignore[arg-type]
        nickname=profile_name,
        plan_name=status.plan_name,
        credits_remaining=status.credits_remaining,
        subscription_status=status.subscription_status,
        needs_onboarding=needs_onboarding,
    )


@app.post("/api/auth/complete-onboarding", response_model=CompleteOnboardingResponse)
async def complete_onboarding(
    payload: CompleteOnboardingRequest,
    db: DbSession,
    current_user=Depends(auth_service.get_current_user),
) -> CompleteOnboardingResponse:
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    user_id = current_user.user_id
    if not _uses_persistent_billing(user_id):
        raise HTTPException(status_code=400, detail="Demo accounts do not require onboarding.")
    if db is None:
        raise HTTPException(status_code=503, detail="Account database is unavailable.")
    if not payload.accepted_terms or not payload.accepted_privacy:
        raise HTTPException(status_code=400, detail="Terms and Privacy Policy must be accepted.")

    uid = UUID(user_id)
    result = await db.execute(
        select(Profile).where(Profile.username == payload.username, Profile.id != uid)
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Username is already taken.")

    profile = await _load_profile(user_id, db)
    now = datetime.now(timezone.utc)
    if profile is None:
        profile = Profile(id=uid, email=current_user.email)
        db.add(profile)
        await db.flush()
    if profile.deleted_at is not None:
        raise HTTPException(status_code=403, detail="This account has been deleted.")

    profile.username = payload.username
    if not profile.nickname:
        profile.nickname = payload.username
    profile.terms_accepted_at = profile.terms_accepted_at or now
    profile.privacy_accepted_at = profile.privacy_accepted_at or now
    profile.onboarded_at = profile.onboarded_at or now
    await db.commit()
    return CompleteOnboardingResponse(username=payload.username, onboarded=True)


@app.post("/api/auth/delete-account", response_model=DeleteAccountResponse)
async def delete_account(
    request: Request,
    db: DbSession,
    current_user=Depends(auth_service.get_current_user),
) -> DeleteAccountResponse:
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    user_id = current_user.user_id
    if not _uses_persistent_billing(user_id):
        raise HTTPException(status_code=400, detail="Demo accounts cannot be deleted.")
    if db is None:
        raise HTTPException(status_code=503, detail="Account database is unavailable.")

    profile = await _load_profile(user_id, db)
    if profile is None:
        profile = Profile(id=UUID(user_id), email=current_user.email)
        db.add(profile)
        await db.flush()

    if profile.deleted_at is None:
        account = await billing_service.async_get_or_create_db_account(user_id, db)
        if account.subscription_status != "free" and account.polar_subscription_id:
            try:
                await billing_service.revoke_polar_subscription(account.polar_subscription_id)
            except (PolarCheckoutConfigError, PolarCheckoutUpstreamError) as exc:
                raise HTTPException(
                    status_code=502,
                    detail="Polar subscription cancellation failed. Please try again or cancel in the customer portal first.",
                ) from exc
        profile.deleted_at = datetime.now(timezone.utc)
        db.add(UserActivityLogDB(
            user_id=UUID(user_id),
            event_type="account_deleted",
            ip_address=request.client.host if request.client else None,
        ))
        account.subscription_status = "free"
        account.plan_name = "Free"
        account.monthly_credit_limit = 0
        account.credits_remaining = 0
        account.polar_subscription_id = None
        await billing_service.async_sync_subscription(
            user_id,
            subscription_status="free",
            plan_name="Free",
            monthly_credit_limit=0,
            polar_subscription_id=None,
            db=db,
        )
        billing_service._accounts.pop(user_id, None)
    await db.commit()
    return DeleteAccountResponse(
        deleted=True,
        message="Account deleted. Activity logs are retained for account history.",
    )


@app.post("/api/billing/checkout", response_model=CheckoutResponse)
async def billing_checkout(
    payload: CheckoutRequest,
    db: DbSession,
    current_user=Depends(auth_service.get_current_user),
) -> CheckoutResponse:
    await _require_active_user(current_user, db)
    if _uses_persistent_billing(current_user.user_id):
        if db is None:
            raise HTTPException(status_code=503, detail="Billing database is unavailable.")
        account = await billing_service.async_get_or_create_db_account(current_user.user_id, db)
        await db.commit()
        if (
            (payload.product_code == "free" or is_recurring_product_code(payload.product_code))
            and account.subscription_status != "free"
        ):
            try:
                portal_url = await billing_service.create_customer_portal_url(
                    current_user.user_id,
                    return_url=payload.success_url,
                )
            except (PolarCheckoutConfigError, PolarCheckoutUpstreamError) as exc:
                raise HTTPException(status_code=502, detail="Failed to create the Polar customer portal.") from exc
            return CheckoutResponse(
                checkout_url=portal_url,
                message="Redirect the user to manage their existing subscription.",
            )
        if payload.product_code == "free":
            return CheckoutResponse(
                checkout_url=payload.success_url or "/",
                message="No active subscription to cancel.",
            )
    try:
        checkout_url = await billing_service.create_checkout_url(
            payload.product_code,
            customer_email=current_user.email,
            user_id=current_user.user_id,
            success_url=payload.success_url,
        )
    except PolarCheckoutConfigError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PolarCheckoutUpstreamError as exc:
        if (
            db is not None
            and _uses_persistent_billing(current_user.user_id)
            and is_recurring_product_code(payload.product_code)
            and "subscription" in str(exc.detail).lower()
        ):
            synced = await billing_service.async_sync_from_polar_customer_state(current_user.user_id, db)
            if synced:
                await db.commit()
            try:
                portal_url = await billing_service.create_customer_portal_url(
                    current_user.user_id,
                    return_url=payload.success_url,
                )
            except (PolarCheckoutConfigError, PolarCheckoutUpstreamError):
                pass
            else:
                return CheckoutResponse(
                    checkout_url=portal_url,
                    message="Redirect the user to manage their existing subscription.",
                )
        raise HTTPException(status_code=502, detail="Failed to create the Polar checkout.") from exc
    return CheckoutResponse(
        checkout_url=checkout_url,
        message="Redirect the user to complete checkout.",
    )


@app.post("/api/webhooks/polar")
async def polar_webhook(request: Request, db: DbSession) -> Response:
    payload = await request.body()
    if not verify_webhook_signature(payload, request.headers):
        raise HTTPException(status_code=403, detail="Invalid webhook signature.")

    event = json.loads(payload)
    event_type: str = event.get("type", "")

    if db is not None:
        if event_type in (
            "subscription.created",
            "subscription.active",
            "subscription.updated",
            "subscription.uncanceled",
            "subscription.canceled",
            "subscription.revoked",
        ):
            await handle_subscription_event(event, db)
        elif event_type in ("order.paid", "order.updated"):
            await handle_order_event(event, db)

    return Response(status_code=200)


frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
frontend_assets = frontend_dist / "assets"
if frontend_dist.exists() and frontend_assets.exists():
    app.mount("/assets", StaticFiles(directory=frontend_assets), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str) -> FileResponse:
        return FileResponse(frontend_dist / "index.html")
