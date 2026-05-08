from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from ..config import get_settings

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class AuthUser:
    user_id: str
    email: str


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthUser | None:
    if not credentials:
        return None
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        user_id: str | None = payload.get("sub")
        email: str = payload.get("email", "")
        if not user_id:
            return None
        return AuthUser(user_id=user_id, email=email)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
