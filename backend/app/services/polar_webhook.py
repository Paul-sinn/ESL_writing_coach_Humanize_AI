from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid
from collections.abc import Mapping
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


def _decode_standard_webhook_secret(secret: str) -> bytes:
    raw_secret = secret.strip()
    for prefix in ("whsec_", "polar_whs_"):
        if raw_secret.startswith(prefix):
            raw_secret = raw_secret[len(prefix):]
            break
    padded = raw_secret + ("=" * (-len(raw_secret) % 4))
    try:
        return base64.b64decode(padded)
    except Exception:
        return secret.encode()


def _extract_standard_webhook_signatures(signature_header: str) -> list[str]:
    signatures: list[str] = []
    for part in signature_header.split():
        if part.startswith("v1,"):
            signatures.append(part.split(",", 1)[1])
        elif part.startswith("v1="):
            signatures.append(part.split("=", 1)[1])
    return signatures


def verify_webhook_signature(payload: bytes, headers: Mapping[str, str]) -> bool:
    """Return True if the request is from Polar using Standard Webhooks signing."""
    secret = settings.polar_webhook_secret
    if not secret:
        return True  # dev mode only

    webhook_id = headers.get("webhook-id")
    timestamp = headers.get("webhook-timestamp")
    signature_header = headers.get("webhook-signature")
    if not webhook_id or not timestamp or not signature_header:
        return False

    try:
        timestamp_int = int(timestamp)
        if abs(time.time() - timestamp_int) > 5 * 60:
            return False
        signed_payload = f"{webhook_id}.{timestamp}.".encode() + payload
        digest = hmac.new(
            _decode_standard_webhook_secret(secret),
            signed_payload,
            hashlib.sha256,
        ).digest()
        expected = base64.b64encode(digest).decode()
        return any(
            hmac.compare_digest(expected, signature)
            for signature in _extract_standard_webhook_signatures(signature_header)
        )
    except Exception:
        return False


def _event_user_id(data: dict[str, Any]) -> str | None:
    metadata = data.get("metadata") or {}
    if isinstance(metadata, dict) and metadata.get("user_id"):
        return str(metadata["user_id"])

    customer = data.get("customer") or {}
    if isinstance(customer, dict) and customer.get("external_id"):
        return str(customer["external_id"])

    if data.get("external_customer_id"):
        return str(data["external_customer_id"])

    customer_metadata = data.get("customer_metadata") or {}
    if isinstance(customer_metadata, dict) and customer_metadata.get("user_id"):
        return str(customer_metadata["user_id"])

    return None


def _event_product_id(data: dict[str, Any]) -> str:
    if data.get("product_id"):
        return str(data["product_id"])
    product = data.get("product") or {}
    if isinstance(product, dict) and product.get("id"):
        return str(product["id"])
    return ""


async def _load_account(user_id: str, db: AsyncSession) -> UserAccountDB | None:
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        return None
    result = await db.execute(select(UserAccountDB).where(UserAccountDB.user_id == uid))
    return result.scalar_one_or_none()


async def handle_subscription_event(event: dict[str, Any], db: AsyncSession) -> None:
    """Handle subscription.created / subscription.updated / subscription.canceled."""
    sub = event.get("data", {})
    polar_sub_id: str = sub.get("id", "")
    product_id = _event_product_id(sub)
    status: str = sub.get("status", "")
    user_id = _event_user_id(sub)

    if not user_id:
        return

    product_map = _build_product_map()
    plan_info = product_map.get(product_id)

    account = await _load_account(user_id, db)
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
    """Handle paid one-time credit pack purchases."""
    order = event.get("data", {})
    if not (order.get("paid") is True or order.get("status") == "paid"):
        return

    product_id = _event_product_id(order)
    user_id = _event_user_id(order)

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

    account = await _load_account(user_id, db)
    if account is None:
        return

    account.credits_remaining += credits_to_add
    await db.commit()
