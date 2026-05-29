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
        await conn.execute(text("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS email TEXT"))
        await conn.execute(text("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS email_hash VARCHAR(64)"))
        await conn.execute(text("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS full_name TEXT"))
        await conn.execute(text("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS full_name_hash VARCHAR(64)"))
        await conn.execute(text("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS terms_accepted_at TIMESTAMPTZ"))
        await conn.execute(text("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS privacy_accepted_at TIMESTAMPTZ"))
        await conn.execute(text("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS onboarded_at TIMESTAMPTZ"))
        await conn.execute(text("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ"))
        await conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_profiles_email_hash "
            "ON profiles (email_hash)"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_profiles_full_name_hash "
            "ON profiles (full_name_hash)"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_profiles_deleted_at "
            "ON profiles (deleted_at)"
        ))
