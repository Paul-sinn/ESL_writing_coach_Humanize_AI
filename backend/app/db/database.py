from __future__ import annotations

import ssl as _ssl
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..config import get_settings

settings = get_settings()

_connect_args: dict = {}
if "localhost" not in settings.database_url and "127.0.0.1" not in settings.database_url:
    _connect_args["ssl"] = _ssl.create_default_context()

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession | None, None]:
    try:
        async with AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    except Exception:
        yield None  # DB unavailable — demo/test mode


DbSession = Annotated[AsyncSession | None, Depends(get_db)]
