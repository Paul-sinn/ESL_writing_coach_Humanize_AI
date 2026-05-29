from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Profile(Base):
    """User profile — id mirrors auth.users.id (managed by Supabase Auth)."""
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=True)
    email_hash = Column(String(64), nullable=True, unique=True, index=True)
    full_name = Column(String, nullable=True)
    full_name_hash = Column(String(64), nullable=True, index=True)
    username = Column(String(50), nullable=True, unique=True, index=True)
    nickname = Column(String(50), nullable=True, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    terms_accepted_at = Column(DateTime(timezone=True), nullable=True)
    privacy_accepted_at = Column(DateTime(timezone=True), nullable=True)
    onboarded_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    account = relationship("UserAccountDB", back_populates="profile", uselist=False, cascade="all, delete-orphan")
    credit_ledger = relationship("CreditLedgerDB", back_populates="profile", cascade="all, delete-orphan")


class UserAccountDB(Base):
    __tablename__ = "user_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, unique=True)
    subscription_status = Column(String(30), nullable=False, default="free")
    credits_remaining = Column(BigInteger, nullable=False, default=0)
    plan_name = Column(String(50), nullable=False, default="Free")
    monthly_credit_limit = Column(BigInteger, nullable=False, default=0)
    polar_subscription_id = Column(String(100), nullable=True, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    profile = relationship("Profile", back_populates="account")


class SubscriptionDB(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, unique=True)
    subscription_status = Column(String(30), nullable=False, default="free")
    plan_name = Column(String(50), nullable=False, default="Free")
    monthly_credit_limit = Column(BigInteger, nullable=False, default=0)
    polar_subscription_id = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class UsageDB(Base):
    __tablename__ = "usage"
    __table_args__ = (
        UniqueConstraint("user_id", "period_key", "feature", name="uq_usage_user_period_feature"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    period_key = Column(String(7), nullable=False, index=True)
    feature = Column(String(30), nullable=False)
    request_count = Column(BigInteger, nullable=False, default=0)
    word_count = Column(BigInteger, nullable=False, default=0)
    credits_used = Column(BigInteger, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class CreditLedgerDB(Base):
    __tablename__ = "credit_ledger"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    feature = Column(String(30), nullable=False)
    amount = Column(BigInteger, nullable=False)
    status = Column(String(30), nullable=False, default="reserved", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    profile = relationship("Profile", back_populates="credit_ledger")


class UserActivityLogDB(Base):
    __tablename__ = "user_activity_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=True, index=True)
    event_type = Column(String(80), nullable=False)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
