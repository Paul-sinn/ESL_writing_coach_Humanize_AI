from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db.models import UserAccountDB

settings = get_settings()

# Map Polar product IDs → (subscription_status, plan_name, monthly_credits)
def _build_product_map() -> dict[str, tuple[str, str, int]]:
    s = get_settings()
    return {
        s.polar_product_id_starter: ("starter", "Starter", s.starter_monthly_credits),
        s.polar_product_id_student_plus: ("student_plus", "Student Plus", s.student_plus_monthly_credits),
        s.polar_product_id_pro: ("pro", "Pro", s.pro_monthly_credits),
    }


def verify_webhook_signature(payload: bytes, signature_header: str | None) -> bool:
    """Return True if the request is from Polar (HMAC-SHA256 over payload)."""
    secret = settings.polar_webhook_secret
    if not secret or not signature_header:
        return not secret  # if no secret configured, allow (dev mode)
    try:
        sig = signature_header.split("=", 1)[1]
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, sig)
    except Exception:
        return False


async def handle_subscription_event(event: dict[str, Any], db: AsyncSession) -> None:
    """Handle subscription.created / subscription.updated / subscription.canceled."""
    sub = event.get("data", {})
    polar_sub_id: str = sub.get("id", "")
    product_id: str = sub.get("product_id", "")
    status: str = sub.get("status", "")
    user_metadata: dict = sub.get("metadata", {}) or {}
    user_id: str | None = user_metadata.get("user_id")

    if not user_id:
        return

    product_map = _build_product_map()
    plan_info = product_map.get(product_id)

    result = await db.execute(
        select(UserAccountDB).where(UserAccountDB.user_id == user_id)
    )
    account = result.scalar_one_or_none()
    if account is None:
        return

    if status == "active" and plan_info:
        new_status, plan_name, monthly_credits = plan_info
        account.subscription_status = new_status
        account.plan_name = plan_name
        account.monthly_credit_limit = monthly_credits
        account.polar_subscription_id = polar_sub_id
        if account.credits_remaining < monthly_credits:
            account.credits_remaining = monthly_credits
    elif status in ("canceled", "revoked"):
        account.subscription_status = "free"
        account.plan_name = "Free"
        account.monthly_credit_limit = 0
        account.polar_subscription_id = None

    await db.commit()


async def handle_order_event(event: dict[str, Any], db: AsyncSession) -> None:
    """Handle order.created for one-time credit pack purchases."""
    order = event.get("data", {})
    product_id: str = order.get("product_id", "")
    user_metadata: dict = order.get("metadata", {}) or {}
    user_id: str | None = user_metadata.get("user_id")

    if not user_id:
        return

    s = get_settings()
    credit_packs: dict[str, int] = {
        s.polar_product_id_credit_s: 25000,
        s.polar_product_id_credit_m: 60000,
        s.polar_product_id_credit_l: 150000,
    }
    credits_to_add = credit_packs.get(product_id, 0)
    if credits_to_add == 0:
        return

    result = await db.execute(
        select(UserAccountDB).where(UserAccountDB.user_id == user_id)
    )
    account = result.scalar_one_or_none()
    if account is None:
        return

    account.credits_remaining += credits_to_add
    await db.commit()
