from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from sqlalchemy import select

from .config import get_settings
from .db.database import DbSession
from .db.models import Profile
from .graphs import calculate_coach_credits, calculate_humanize_credits, coach_graph, humanize_graph
from .schemas import (
    BillingStatusResponse,
    CheckoutRequest,
    CheckoutResponse,
    CoachRequest,
    CoachResponse,
    DemoLoginRequest,
    DemoLoginResponse,
    HumanizeRequest,
    HumanizeResponse,
    UserResponse,
)
from .services import auth as auth_service
from .services.billing import PolarCheckoutConfigError, PolarCheckoutUpstreamError, billing_service
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from .db.init_db import create_tables
        await create_tables()
        print("✅ DB tables created / verified.")
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
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required.")
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
            await db.commit()
    except Exception:
        if reserved_ledger_id is not None and db is not None:
            await billing_service.async_release_reservation(reserved_ledger_id, db)
            await db.commit()
        raise

    return response


@app.post("/api/humanize", response_model=HumanizeResponse)
async def humanize(
    payload: HumanizeRequest,
    db: DbSession,
    current_user=Depends(auth_service.get_current_user),
) -> HumanizeResponse:
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required.")
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
            await db.commit()
    except Exception:
        if reserved_ledger_id is not None and db is not None:
            await billing_service.async_release_reservation(reserved_ledger_id, db)
            await db.commit()
        raise

    return response


@app.get("/api/billing/status", response_model=BillingStatusResponse)
async def billing_status(
    db: DbSession,
    current_user=Depends(auth_service.get_current_user),
) -> BillingStatusResponse:
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    user_id = current_user.user_id
    if db is not None and _uses_persistent_billing(user_id):
        try:
            await billing_service.async_load_to_memory(user_id, db)
        except Exception:
            pass
    return billing_service.get_status(user_id)


@app.get("/api/auth/check-username")
async def check_username(username: str, db: DbSession) -> dict:
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
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    user_id = current_user.user_id
    profile = None
    if db is not None and _uses_persistent_billing(user_id):
        try:
            result = await db.execute(select(Profile).where(Profile.id == user_id))
            profile = result.scalar_one_or_none()
            await billing_service.async_load_to_memory(user_id, db)
        except Exception:
            profile = None
    status = billing_service.get_status(user_id)
    return UserResponse(
        email=current_user.email,
        username=profile.username if profile else None,  # type: ignore[arg-type]
        nickname=profile.nickname if profile else None,  # type: ignore[arg-type]
        plan_name=status.plan_name,
        credits_remaining=status.credits_remaining,
        subscription_status=status.subscription_status,
    )


@app.post("/api/billing/checkout", response_model=CheckoutResponse)
async def billing_checkout(
    payload: CheckoutRequest,
    current_user=Depends(auth_service.get_current_user),
) -> CheckoutResponse:
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required.")
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
        raise HTTPException(status_code=502, detail="Polar checkout 생성에 실패했습니다.") from exc
    return CheckoutResponse(
        checkout_url=checkout_url,
        message="Redirect the user to complete checkout.",
    )


@app.post("/api/webhooks/polar")
async def polar_webhook(request: Request, db: DbSession) -> Response:
    payload = await request.body()
    sig = request.headers.get("webhook-signature")
    if not verify_webhook_signature(payload, sig):
        raise HTTPException(status_code=403, detail="Invalid webhook signature.")

    event = json.loads(payload)
    event_type: str = event.get("type", "")

    if db is not None:
        if event_type in ("subscription.created", "subscription.updated", "subscription.canceled"):
            await handle_subscription_event(event, db)
        elif event_type == "order.created":
            await handle_order_event(event, db)

    return Response(status_code=200)


frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str) -> FileResponse:
        return FileResponse(frontend_dist / "index.html")
