from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parseaddr

import httpx

from ..config import get_settings
from ..schemas import BillingRedirect, BillingStatusResponse, CheckoutOption

try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from ..db.models import CreditLedgerDB as _CreditLedgerDBModel
    from ..db.models import SubscriptionDB as _SubscriptionDBModel
    from ..db.models import UsageDB as _UsageDBModel
    from ..db.models import UserAccountDB as _UserAccountDBModel
    _DB_AVAILABLE = True
except Exception:
    _DB_AVAILABLE = False


@dataclass
class UserAccount:
    user_id: str
    subscription_status: str
    credits_remaining: int


class PolarCheckoutConfigError(ValueError):
    pass


class PolarCheckoutUpstreamError(RuntimeError):
    def __init__(self, detail: str, status_code: int | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


settings = get_settings()
_RESERVED_EMAIL_DOMAINS = {
    "example.com",
    "example.net",
    "example.org",
    "invalid",
    "localhost",
    "test",
}

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


def _current_period_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _polar_product_ids() -> dict[str, str]:
    return {
        "starter_monthly": settings.polar_product_id_starter,
        "student_plus_monthly": settings.polar_product_id_student_plus,
        "pro_monthly": settings.polar_product_id_pro,
        "credit_pack_s": settings.polar_product_id_credit_s,
        "credit_pack_m": settings.polar_product_id_credit_m,
        "credit_pack_l": settings.polar_product_id_credit_l,
    }


def _is_safe_customer_email(email: str | None) -> bool:
    if not email:
        return False
    _, parsed = parseaddr(email)
    if parsed != email or "@" not in parsed:
        return False
    domain = parsed.rsplit("@", 1)[1].lower()
    suffix = domain.rsplit(".", 1)[-1]
    return domain not in _RESERVED_EMAIL_DOMAINS and suffix not in _RESERVED_EMAIL_DOMAINS


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
        monthly_limit = _MONTHLY_CREDIT_LIMITS.get(account.subscription_status, 0)
        usage_used = max(0, monthly_limit - account.credits_remaining) if monthly_limit > 0 else 0
        usage_percent = min(100, round((usage_used / monthly_limit) * 100)) if monthly_limit > 0 else 0
        return BillingStatusResponse(
            subscription_status=account.subscription_status,  # type: ignore[arg-type]
            credits_remaining=account.credits_remaining,
            plan_name=_PLAN_NAMES.get(account.subscription_status, "Free"),
            monthly_credit_limit=monthly_limit,
            usage_used=usage_used,
            usage_limit=monthly_limit,
            usage_percent=usage_percent,
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

    async def create_checkout_url(
        self,
        product_code: str,
        *,
        customer_email: str | None = None,
        user_id: str | None = None,
        success_url: str | None = None,
    ) -> str:
        product_id = _polar_product_ids().get(product_code)
        if product_id is None:
            raise PolarCheckoutConfigError("Unsupported product code.")
        if not product_id:
            raise PolarCheckoutConfigError(f"Polar product ID is not configured for {product_code}.")
        if not settings.polar_access_token:
            raise PolarCheckoutConfigError("Polar access token is not configured.")

        body: dict[str, object] = {"products": [product_id]}
        if success_url:
            body["success_url"] = success_url
        if _is_safe_customer_email(customer_email):
            body["customer_email"] = customer_email
        if user_id:
            body["external_customer_id"] = user_id
            body["metadata"] = {"user_id": user_id}

        endpoint = f"{settings.polar_api_base_url.rstrip('/')}/v1/checkouts/"
        headers = {
            "Authorization": f"Bearer {settings.polar_access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "pj-1-humanize-app/0.1 server-checkout",
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(endpoint, json=body, headers=headers)
        except httpx.RequestError as exc:
            detail = str(exc)
            print(f"Polar checkout request failed: {detail}")
            raise PolarCheckoutUpstreamError(detail) from exc

        if response.status_code >= 400:
            detail = response.text
            print(f"Polar checkout failed ({response.status_code}): {detail}")
            raise PolarCheckoutUpstreamError(detail, status_code=response.status_code)

        try:
            payload = response.json()
        except ValueError as exc:
            detail = response.text
            print(f"Polar checkout returned invalid JSON: {detail}")
            raise PolarCheckoutUpstreamError("Polar checkout response was not valid JSON.") from exc

        checkout_url = payload.get("url") or payload.get("checkout_url")
        if not isinstance(checkout_url, str) or not checkout_url:
            raise PolarCheckoutUpstreamError("Polar checkout response did not include a checkout URL.")
        return checkout_url

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
        sub_result = await db.execute(
            select(_SubscriptionDBModel).where(_SubscriptionDBModel.user_id == uid)
        )
        subscription = sub_result.scalar_one_or_none()
        if subscription is None:
            db.add(_SubscriptionDBModel(
                user_id=uid,
                subscription_status=account.subscription_status,
                plan_name=account.plan_name,
                monthly_credit_limit=account.monthly_credit_limit,
                polar_subscription_id=account.polar_subscription_id,
            ))
            await db.flush()
        return account

    async def async_sync_subscription(
        self,
        user_id: str,
        *,
        subscription_status: str,
        plan_name: str,
        monthly_credit_limit: int,
        polar_subscription_id: str | None,
        db: "AsyncSession",
    ) -> None:
        uid = uuid.UUID(user_id)
        result = await db.execute(
            select(_SubscriptionDBModel).where(_SubscriptionDBModel.user_id == uid)
        )
        subscription = result.scalar_one_or_none()
        if subscription is None:
            subscription = _SubscriptionDBModel(user_id=uid)
            db.add(subscription)
        subscription.subscription_status = subscription_status
        subscription.plan_name = plan_name
        subscription.monthly_credit_limit = monthly_credit_limit
        subscription.polar_subscription_id = polar_subscription_id

    async def async_record_usage(
        self,
        user_id: str,
        *,
        feature: str,
        words: int,
        credits_used: int,
        db: "AsyncSession",
    ) -> None:
        account = await self.async_get_or_create_db_account(user_id, db)
        if account.subscription_status == "unlimited" or account.monthly_credit_limit < 0:
            return

        uid = uuid.UUID(user_id)
        period_key = _current_period_key()
        result = await db.execute(
            select(_UsageDBModel).where(
                _UsageDBModel.user_id == uid,
                _UsageDBModel.period_key == period_key,
                _UsageDBModel.feature == feature,
            )
        )
        usage = result.scalar_one_or_none()
        if usage is None:
            usage = _UsageDBModel(
                user_id=uid,
                period_key=period_key,
                feature=feature,
                request_count=0,
                word_count=0,
                credits_used=0,
            )
            db.add(usage)
        usage.request_count += 1
        usage.word_count += max(0, words)
        usage.credits_used += max(0, credits_used)

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
