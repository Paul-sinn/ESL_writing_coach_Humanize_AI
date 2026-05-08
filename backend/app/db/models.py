from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String
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
    username = Column(String(50), nullable=True, unique=True, index=True)
    nickname = Column(String(50), nullable=True, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

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
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    profile = relationship("Profile", back_populates="account")


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
