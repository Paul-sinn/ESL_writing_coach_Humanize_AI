from __future__ import annotations

from sqlalchemy import text

from .database import engine
from .models import Base


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text(
            "ALTER TABLE user_accounts ADD COLUMN IF NOT EXISTS "
            "polar_subscription_id VARCHAR(100)"
        ))
