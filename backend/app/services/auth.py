from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import bcrypt
import jwt as pyjwt
from jwt import PyJWKClient, PyJWKClientConnectionError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from ..config import get_settings
from ..db.models import Profile

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)

_jwks_client: PyJWKClient | None = None
_verified_emails: set[str] = set()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))


def create_access_token(data: dict) -> str:
    payload = data.copy()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload["exp"] = expires_at
    return pyjwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def register(email: str, username: str, nickname: str, password: str, db) -> str:
    existing_email = await db.execute(select(Profile).where(Profile.username == email))
    if existing_email.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Email is already registered.")

    existing_username = await db.execute(select(Profile).where(Profile.username == username))
    if existing_username.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Username is already taken.")

    user_id = str(uuid4())
    user = SimpleNamespace(
        id=user_id,
        email=email,
        username=username,
        nickname=nickname,
        hashed_password=hash_password(password),
        is_active=True,
    )
    db.add(user)
    await db.flush()
    _verified_emails.add(email)
    return create_access_token({"sub": user_id, "email": email, "username": username, "nickname": nickname})


async def login(email: str, password: str, db) -> tuple[str, str | None, str | None]:
    result = await db.execute(select(Profile).where(Profile.username == email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "username": user.username,
            "nickname": user.nickname,
        }
    )
    return token, user.username, user.nickname


def _get_jwks_client() -> PyJWKClient | None:
    global _jwks_client
    if _jwks_client is None and settings.supabase_url:
        _jwks_client = PyJWKClient(f"{settings.supabase_url}/auth/v1/.well-known/jwks.json")
    return _jwks_client


@dataclass
class AuthUser:
    user_id: str
    email: str


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthUser | None:
    if not credentials:
        return None
    token = credentials.credentials
    try:
        jwks = _get_jwks_client()
        if jwks:
            signing_key = jwks.get_signing_key_from_jwt(token)
            payload = pyjwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256", "RS256", "HS256"],
                audience="authenticated",
            )
        elif settings.supabase_jwt_secret:
            payload = pyjwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
        else:
            raise HTTPException(status_code=401, detail="Auth not configured.")

        user_id: str | None = payload.get("sub")
        email: str = payload.get("email", "")
        if not user_id:
            return None
        return AuthUser(user_id=user_id, email=email)
    except (pyjwt.PyJWTError, PyJWKClientConnectionError):
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
