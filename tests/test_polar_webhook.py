import base64
import hashlib
import hmac
import json
import time
from types import SimpleNamespace

from backend.app.services import polar_webhook
from backend.app.services.polar_webhook import (
    handle_order_event,
    handle_subscription_event,
    verify_webhook_signature,
)


def _signed_headers(payload: bytes, secret: str, timestamp: int | None = None) -> dict[str, str]:
    webhook_id = "msg_test"
    webhook_timestamp = str(timestamp or int(time.time()))
    key = base64.b64decode(secret.removeprefix("polar_whs_"))
    signed_payload = f"{webhook_id}.{webhook_timestamp}.".encode() + payload
    signature = base64.b64encode(hmac.new(key, signed_payload, hashlib.sha256).digest()).decode()
    return {
        "webhook-id": webhook_id,
        "webhook-timestamp": webhook_timestamp,
        "webhook-signature": f"v1,{signature}",
    }


def test_verify_polar_standard_webhook_signature(monkeypatch):
    secret = "polar_whs_" + base64.b64encode(b"test-webhook-secret-32-bytes!!").decode()
    payload = b'{"type":"subscription.active"}'
    monkeypatch.setattr(polar_webhook.settings, "polar_webhook_secret", secret)

    assert verify_webhook_signature(payload, _signed_headers(payload, secret))


def test_verify_polar_standard_webhook_signature_rejects_old_timestamp(monkeypatch):
    secret = "polar_whs_" + base64.b64encode(b"test-webhook-secret-32-bytes!!").decode()
    payload = b'{"type":"subscription.active"}'
    monkeypatch.setattr(polar_webhook.settings, "polar_webhook_secret", secret)

    headers = _signed_headers(payload, secret, timestamp=int(time.time()) - 600)

    assert not verify_webhook_signature(payload, headers)


def test_subscription_event_uses_customer_external_id(monkeypatch):
    account = SimpleNamespace(
        subscription_status="free",
        plan_name="Free",
        monthly_credit_limit=0,
        polar_subscription_id=None,
        credits_remaining=0,
    )
    db = SimpleNamespace(commit=lambda: None)

    async def fake_commit():
        return None

    async def fake_load_account(user_id, db):
        assert user_id == "00000000-0000-0000-0000-000000000001"
        return account

    synced = {}

    async def fake_sync_subscription(user_id, **kwargs):
        synced["user_id"] = user_id
        synced.update(kwargs)

    db.commit = fake_commit
    monkeypatch.setattr(polar_webhook, "_load_account", fake_load_account)
    monkeypatch.setattr(polar_webhook.billing_service, "async_sync_subscription", fake_sync_subscription)
    monkeypatch.setattr(polar_webhook.settings, "polar_product_id_student_plus", "product-plus")

    import asyncio

    asyncio.run(handle_subscription_event(
        {
            "type": "subscription.active",
            "data": {
                "id": "sub_123",
                "status": "active",
                "product_id": "product-plus",
                "metadata": {},
                "customer": {"external_id": "00000000-0000-0000-0000-000000000001"},
            },
        },
        db,
    ))

    assert account.subscription_status == "student_plus"
    assert account.plan_name == "Student Plus"
    assert account.monthly_credit_limit == 60000
    assert account.credits_remaining == 60000
    assert account.polar_subscription_id == "sub_123"
    assert synced["subscription_status"] == "student_plus"


def test_order_event_only_grants_paid_credit_pack(monkeypatch):
    account = SimpleNamespace(credits_remaining=0)
    db = SimpleNamespace(commit=lambda: None)

    async def fake_commit():
        return None

    async def fake_load_account(user_id, db):
        assert user_id == "00000000-0000-0000-0000-000000000001"
        return account

    db.commit = fake_commit
    monkeypatch.setattr(polar_webhook, "_load_account", fake_load_account)
    monkeypatch.setattr(polar_webhook.settings, "polar_product_id_credit_s", "product-credit-s")

    import asyncio

    event = {
        "type": "order.created",
        "data": {
            "paid": False,
            "status": "pending",
            "product_id": "product-credit-s",
            "customer": {"external_id": "00000000-0000-0000-0000-000000000001"},
        },
    }
    asyncio.run(handle_order_event(json.loads(json.dumps(event)), db))
    assert account.credits_remaining == 0

    event["type"] = "order.paid"
    event["data"]["paid"] = True
    event["data"]["status"] = "paid"
    asyncio.run(handle_order_event(event, db))
    assert account.credits_remaining == 25000
