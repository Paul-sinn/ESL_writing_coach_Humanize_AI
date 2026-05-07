from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt as _bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db.database import DbSession
from ..db.models import User, UserAccountDB

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)

_verified_emails: set[str] = set()


def hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def register(email: str, username: str, nickname: str, password: str, db: AsyncSession) -> str:
    if (await db.execute(select(User).where(User.email == email))).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email is already in use.")
    if (await db.execute(select(User).where(User.username == username))).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username is already taken.")

    user = User(email=email, username=username, nickname=nickname, hashed_password=hash_password(password))
    db.add(user)
    await db.flush()

    account = UserAccountDB(
        user_id=user.id,
        subscription_status="free",
        credits_remaining=0,
        plan_name="Free",
        monthly_credit_limit=0,
    )
    db.add(account)
    _verified_emails.add(email)

    return create_access_token({"sub": str(user.id), "email": user.email, "username": username, "nickname": nickname})


async def login(email: str, password: str, db: AsyncSession) -> tuple[str, str | None, str | None]:
    result = await db.execute(select(User).where(User.email == email, User.is_active == True))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    token = create_access_token({"sub": str(user.id), "email": user.email, "username": user.username, "nickname": user.nickname})
    return token, user.username, user.nickname

async def change_password(user:User,current_password:str,new_password:str,db:AsyncSession) -> None:
    if not verify_password(current_password,user.hashed_password):
        raise HTTPException(status_code=401,detail="The Password is not correct.")
    user.hashed_password = hash_password(new_password)
    db.add(user)
    
async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: DbSession = None,
) -> User | None:
    if not credentials:
        return None
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id: str | None = payload.get("sub")
        if not user_id:
            return None
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    if db is None:
        return None

    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    return result.scalar_one_or_none()
