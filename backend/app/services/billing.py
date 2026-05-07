from __future__ import annotations

import uuid
from dataclasses import dataclass

from ..config import get_settings
from ..schemas import BillingRedirect, BillingStatusResponse, CheckoutOption

try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from ..db.models import CreditLedgerDB as _CreditLedgerDBModel
    from ..db.models import UserAccountDB as _UserAccountDBModel
    _DB_AVAILABLE = True
except Exception:
    _DB_AVAILABLE = False


@dataclass
class UserAccount:
    user_id: str
    subscription_status: str
    credits_remaining: int


settings = get_settings()

CHECKOUT_OPTIONS = [
    CheckoutOption(
        code="starter_monthly",
        label="Starter · $7/month",
        price_usd=7,
        credits=settings.starter_monthly_credits,
        description="20,000 credits/month for light users.",
    ),
    CheckoutOption(
        code="student_plus_monthly",
        label="Student Plus · $12/month",
        price_usd=12,
        credits=settings.student_plus_monthly_credits,
        description="60,000 credits/month. Most popular.",
    ),
    CheckoutOption(
        code="pro_monthly",
        label="Pro · $19/month",
        price_usd=19,
        credits=settings.pro_monthly_credits,
        description="150,000 credits/month for power users.",
    ),
    CheckoutOption(
        code="credit_pack_s",
        label="$5 credit pack",
        price_usd=5,
        credits=25000,
        description="25,000 one-time credits.",
    ),
    CheckoutOption(
        code="credit_pack_m",
        label="$10 credit pack",
        price_usd=10,
        credits=60000,
        description="60,000 one-time credits.",
    ),
    CheckoutOption(
        code="credit_pack_l",
        label="$20 credit pack",
        price_usd=20,
        credits=150000,
        description="150,000 one-time credits.",
    ),
]

_PLAN_NAMES = {
    "free": "Free",
    "starter": "Starter",
    "student_plus": "Student Plus",
    "pro": "Pro",
}

_MONTHLY_CREDIT_LIMITS = {
    "free": 0,
    "starter": settings.starter_monthly_credits,
    "student_plus": settings.student_plus_monthly_credits,
    "pro": settings.pro_monthly_credits,
}


class BillingService:
    def __init__(self) -> None:
        self._accounts: dict[str, UserAccount] = {
            "demo-free": UserAccount("demo-free", "free", 0),
            "demo-starter": UserAccount("demo-starter", "starter", 20000),
            "demo-plus": UserAccount("demo-plus", "student_plus", 60000),
            "demo-pro": UserAccount("demo-pro", "pro", 150000),
        }

    def get_or_create_account(self, user_id: str) -> UserAccount:
        return self._accounts.setdefault(user_id, UserAccount(user_id, "free", 0))

    def get_status(self, user_id: str) -> BillingStatusResponse:
        account = self.get_or_create_account(user_id)
        return BillingStatusResponse(
            subscription_status=account.subscription_status,  # type: ignore[arg-type]
            credits_remaining=account.credits_remaining,
            plan_name=_PLAN_NAMES.get(account.subscription_status, "Free"),
            monthly_credit_limit=_MONTHLY_CREDIT_LIMITS.get(account.subscription_status, 0),
            available_credit_packs=CHECKOUT_OPTIONS,
        )

    def ensure_credits(self, user_id: str, credits_required: int) -> tuple[bool, UserAccount]:
        account = self.get_or_create_account(user_id)
        return account.credits_remaining >= credits_required, account

    def deduct_credits(self, user_id: str, credits_required: int) -> UserAccount:
        account = self.get_or_create_account(user_id)
        if credits_required <= 0:
            return account
        if account.credits_remaining < credits_required:
            raise ValueError("Insufficient credits.")
        account.credits_remaining -= credits_required
        return account

    def build_redirect(self, user_id: str, trigger_action: str) -> BillingRedirect:
        account = self.get_or_create_account(user_id)
        if account.subscription_status == "free":
            offer = "Upgrade to Student Plus to get 60,000 credits/month."
        else:
            offer = "Buy a credit pack to top up and continue."
        return BillingRedirect(
            route="/billing",
            message=f"You need more credits to use {trigger_action}.",
            recommended_offer=offer,
            checkout_options=CHECKOUT_OPTIONS,
        )

    def create_checkout_url(self, product_code: str) -> str:
        return f"https://billing.example.com/checkout/{product_code}"

    # ── Async DB methods (real users only) ────────────────────────────────────

    async def async_get_or_create_db_account(self, user_id: str, db: "AsyncSession") -> "_UserAccountDBModel":
        uid = uuid.UUID(user_id)
        result = await db.execute(
            select(_UserAccountDBModel).where(_UserAccountDBModel.user_id == uid)
        )
        account = result.scalar_one_or_none()
        if account is None:
            account = _UserAccountDBModel(
                user_id=uid,
                subscription_status="free",
                credits_remaining=0,
                plan_name="Free",
                monthly_credit_limit=0,
            )
            db.add(account)
            await db.flush()
        return account

    async def async_load_to_memory(self, user_id: str, db: "AsyncSession") -> None:
        """Sync real user's DB credits into in-memory dict so graph nodes can read them."""
        account = await self.async_get_or_create_db_account(user_id, db)
        self._accounts[user_id] = UserAccount(
            user_id=user_id,
            subscription_status=account.subscription_status,
            credits_remaining=account.credits_remaining,
        )

    async def async_deduct_credits(self, user_id: str, amount: int, db: "AsyncSession") -> None:
        """Persist credit deduction to DB with row-level lock."""
        if amount <= 0:
            return
        result = await db.execute(
            select(_UserAccountDBModel)
            .where(_UserAccountDBModel.user_id == uuid.UUID(user_id))
            .with_for_update()
        )
        account = result.scalar_one()
        account.credits_remaining = max(0, account.credits_remaining - amount)
        self._accounts[user_id] = UserAccount(
            user_id=user_id,
            subscription_status=account.subscription_status,
            credits_remaining=account.credits_remaining,
        )

    async def async_reserve_credits(self, user_id: str, amount: int, feature: str, db: "AsyncSession") -> int:
        if amount <= 0:
            raise ValueError("Reservation amount must be positive.")
        uid = uuid.UUID(user_id)
        result = await db.execute(
            select(_UserAccountDBModel)
            .where(_UserAccountDBModel.user_id == uid)
            .with_for_update()
        )
        account = result.scalar_one()
        if account.credits_remaining < amount:
            raise ValueError("Insufficient credits.")
        account.credits_remaining -= amount
        ledger = _CreditLedgerDBModel(
            user_id=uid,
            feature=feature,
            amount=amount,
            status="reserved",
        )
        db.add(ledger)
        await db.flush()
        self._accounts[user_id] = UserAccount(
            user_id=user_id,
            subscription_status=account.subscription_status,
            credits_remaining=account.credits_remaining,
        )
        return int(ledger.id)

    async def async_capture_reservation(self, ledger_id: int, db: "AsyncSession") -> None:
        result = await db.execute(
            select(_CreditLedgerDBModel)
            .where(_CreditLedgerDBModel.id == ledger_id)
            .with_for_update()
        )
        ledger = result.scalar_one()
        if ledger.status == "reserved":
            ledger.status = "charged"

    async def async_release_reservation(self, ledger_id: int, db: "AsyncSession") -> None:
        result = await db.execute(
            select(_CreditLedgerDBModel)
            .where(_CreditLedgerDBModel.id == ledger_id)
            .with_for_update()
        )
        ledger = result.scalar_one()
        if ledger.status != "reserved":
            return
        account_result = await db.execute(
            select(_UserAccountDBModel)
            .where(_UserAccountDBModel.user_id == ledger.user_id)
            .with_for_update()
        )
        account = account_result.scalar_one()
        account.credits_remaining += ledger.amount
        ledger.status = "released"
        self._accounts[str(account.user_id)] = UserAccount(
            user_id=str(account.user_id),
            subscription_status=account.subscription_status,
            credits_remaining=account.credits_remaining,
        )


billing_service = BillingService()
