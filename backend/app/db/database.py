from __future__ import annotations

import ssl as _ssl
import certifi
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..config import get_settings

settings = get_settings()

_connect_args: dict = {}
if "localhost" not in settings.database_url and "127.0.0.1" not in settings.database_url:
    if settings.database_ssl_verify:
        _connect_args["ssl"] = _ssl.create_default_context(cafile=certifi.where())
    else:
        ssl_context = _ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = _ssl.CERT_NONE
        _connect_args["ssl"] = ssl_context

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
    yielded = False
    try:
        async with AsyncSessionLocal() as session:
            yielded = True
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
    except Exception:
        if yielded:
            raise
        yield None  # DB unavailable before request handling starts.


DbSession = Annotated[AsyncSession | None, Depends(get_db)]
