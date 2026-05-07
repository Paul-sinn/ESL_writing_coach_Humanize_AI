from __future__ import annotations

from sqlalchemy import text

from .database import engine
from .models import Base

_MIGRATIONS = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(50)",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS nickname VARCHAR(50)",
    # Partial unique indexes: allow multiple NULLs, enforce uniqueness on non-NULL values
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users (username) WHERE username IS NOT NULL",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_nickname ON users (nickname) WHERE nickname IS NOT NULL",
]


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for stmt in _MIGRATIONS:
            try:
                await conn.execute(text(stmt))
            except Exception as e:
                print(f"⚠️  Migration skipped ({e}): {stmt[:60]}")
