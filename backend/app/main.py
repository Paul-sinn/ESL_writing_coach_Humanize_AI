from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from sqlalchemy import select

from .config import get_settings
from .db.database import DbSession
from .db.models import User
from .graphs import calculate_coach_credits, calculate_humanize_credits, coach_graph, humanize_graph
from .schemas import (
    BillingStatusResponse,
    CheckoutRequest,
    CheckoutResponse,
    CoachRequest,
    CoachResponse,
    HumanizeRequest,
    HumanizeResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    ChangePasswordRequest
)
from .services import auth as auth_service
from .services.billing import billing_service
from .utils.text import count_words


settings = get_settings()


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


def get_user_id(x_user_id: str | None) -> str:
    return x_user_id or "demo-pro"


def _is_real_user(user_id: str) -> bool:
    return not user_id.startswith("demo-")


async def _reserve_real_user_credits(
    user_id: str,
    amount: int,
    feature: str,
    db,
) -> int | None:
    if not _is_real_user(user_id) or db is None or amount <= 0:
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
    request: Request,
    db: DbSession,
    x_user_id: str | None = Header(default=None),
) -> CoachResponse:
    user_id = get_user_id(x_user_id)
    client_ip = request.client.host if request.client else "unknown"
    reserved_ledger_id: int | None = None

    if _is_real_user(user_id) and db is not None:
        await billing_service.async_load_to_memory(user_id, db)
        status = billing_service.get_status(user_id)
        if status.subscription_status != "free":
            credits_required = calculate_coach_credits(count_words(payload.text), payload.depth)
            reserved_ledger_id = await _reserve_real_user_credits(user_id, credits_required, "coach", db)

    try:
        result = coach_graph.invoke({
            "user_id": user_id,
            "client_ip": client_ip,
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
    x_user_id: str | None = Header(default=None),
) -> HumanizeResponse:
    user_id = get_user_id(x_user_id)
    reserved_ledger_id: int | None = None

    if _is_real_user(user_id) and db is not None:
        await billing_service.async_load_to_memory(user_id, db)
        status = billing_service.get_status(user_id)
        if status.subscription_status != "free":
            credits_required = calculate_humanize_credits(count_words(payload.text))
            reserved_ledger_id = await _reserve_real_user_credits(user_id, credits_required, "humanize", db)

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
    x_user_id: str | None = Header(default=None),
) -> BillingStatusResponse:
    user_id = get_user_id(x_user_id)
    if _is_real_user(user_id) and db is not None:
        await billing_service.async_load_to_memory(user_id, db)
    return billing_service.get_status(user_id)


@app.get("/api/auth/check-email")
async def check_email(email: str, db: DbSession) -> dict:
    if db is None:
        return {"available": True}
    result = await db.execute(select(User).where(User.email == email))
    return {"available": result.scalar_one_or_none() is None}


@app.get("/api/auth/check-username")
async def check_username(username: str, db: DbSession) -> dict:
    if db is None:
        return {"available": True}
    result = await db.execute(select(User).where(User.username == username))
    return {"available": result.scalar_one_or_none() is None}


@app.get("/api/auth/check-nickname")
async def check_nickname(nickname: str, db: DbSession) -> dict:
    if db is None:
        return {"available": True}
    result = await db.execute(select(User).where(User.nickname == nickname))
    return {"available": result.scalar_one_or_none() is None}


@app.post("/api/auth/register", status_code=201, response_model=TokenResponse)
async def auth_register(payload: RegisterRequest, db: DbSession) -> TokenResponse:
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")
    token = await auth_service.register(payload.email, payload.username, payload.nickname, payload.password, db)
    return TokenResponse(
        access_token=token,
        email=payload.email,
        username=payload.username,
        nickname=payload.nickname,
        plan_name="Free",
        credits_remaining=0,
    )



@app.post("/api/auth/login", response_model=TokenResponse)
async def auth_login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")
    token, username, nickname = await auth_service.login(payload.email, payload.password, db)
    return TokenResponse(
        access_token=token,
        email=payload.email,
        username=username,
        nickname=nickname,
        plan_name="Free",
        credits_remaining=0,
    )


@app.get("/api/auth/me", response_model=UserResponse)
async def auth_me(
    db: DbSession,
    current_user=Depends(auth_service.get_current_user),
) -> UserResponse:
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    if db is not None:
        await billing_service.async_load_to_memory(str(current_user.id), db)
    status = billing_service.get_status(str(current_user.id))
    return UserResponse(
        email=current_user.email,
        username=current_user.username,
        nickname=current_user.nickname,
        plan_name=status.plan_name,
        credits_remaining=status.credits_remaining,
        subscription_status=status.subscription_status,
    )


@app.post("/api/billing/checkout", response_model=CheckoutResponse)
async def billing_checkout(payload: CheckoutRequest) -> CheckoutResponse:
    valid_codes = {
        "starter_monthly", "student_plus_monthly", "pro_monthly",
        "credit_pack_s", "credit_pack_m", "credit_pack_l",
    }
    if payload.product_code not in valid_codes:
        raise HTTPException(status_code=400, detail="Unsupported product code.")
    return CheckoutResponse(
        checkout_url=billing_service.create_checkout_url(payload.product_code),
        message="Redirect the user to complete checkout.",
    )

@app.patch("/api/auth/password", status_code= 204)
async def change_password(payload: ChangePasswordRequest, db: DbSession, current_user = Depends(auth_service.get_current_user),) -> None:
    if not current_user:
        raise HTTPException(status_code=401, detail="Please Login")
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")
    await auth_service.change_password(
        current_user, payload.current_password, payload.new_password, db
    )


frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str) -> FileResponse:
        return FileResponse(frontend_dist / "index.html")
