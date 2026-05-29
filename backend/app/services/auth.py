from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt as pyjwt
from jwt import PyJWKClient, PyJWKClientConnectionError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..config import get_settings

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)

_jwks_client: PyJWKClient | None = None


def create_access_token(data: dict) -> str:
    payload = data.copy()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload["exp"] = expires_at
    return pyjwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_demo_access_token(email: str) -> str:
    return create_access_token(
        {
            "sub": settings.demo_login_user_id,
            "email": email,
            "username": "demo",
            "nickname": "Demo Student",
            "demo": True,
        }
    )


def verify_demo_credentials(email: str, password: str) -> bool:
    return (
        settings.demo_login_enabled
        and email.strip().lower() == settings.demo_login_email.lower()
        and password == settings.demo_login_password
    )


def _decode_local_app_token(token: str) -> dict | None:
    if not settings.demo_login_enabled:
        return None
    try:
        payload = pyjwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except pyjwt.PyJWTError:
        return None
    if payload.get("demo") is not True:
        return None
    return payload


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
    auth_error: Exception | None = None
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
    except (pyjwt.PyJWTError, PyJWKClientConnectionError) as exc:
        auth_error = exc

    payload = _decode_local_app_token(token)
    if payload:
        user_id = payload.get("sub")
        email = payload.get("email", "")
        if user_id:
            return AuthUser(user_id=user_id, email=email)

    raise HTTPException(status_code=401, detail="Invalid or expired token.") from auth_error
