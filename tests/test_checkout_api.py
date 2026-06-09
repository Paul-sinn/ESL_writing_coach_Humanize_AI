from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend.app.db.database import get_db
from backend.app.main import app
from backend.app.services import auth as auth_service
from backend.app.services.auth import AuthUser
from backend.app.services.billing import PolarCheckoutConfigError, PolarCheckoutUpstreamError


class FakeDb:
    async def execute(self, _statement):
        return SimpleNamespace(scalar_one_or_none=lambda: None)

    async def commit(self):
        return None


def _auth_user() -> AuthUser:
    return AuthUser(
        user_id="00000000-0000-0000-0000-000000000001",
        email="student@example.com",
    )


async def _fake_db():
    yield FakeDb()


async def _fake_get_or_create_account(*args, **kwargs):
    return SimpleNamespace(subscription_status="free")


def test_checkout_config_error_returns_400(monkeypatch):
    async def fake_create_checkout_url(*args, **kwargs):
        raise PolarCheckoutConfigError("Polar access token is not configured.")

    monkeypatch.setattr("backend.app.main.billing_service.create_checkout_url", fake_create_checkout_url)
    monkeypatch.setattr("backend.app.main.billing_service.async_get_or_create_db_account", _fake_get_or_create_account)
    app.dependency_overrides[auth_service.get_current_user] = _auth_user
    app.dependency_overrides[get_db] = _fake_db
    try:
        response = TestClient(app).post(
            "/api/billing/checkout",
            json={"product_code": "starter_monthly", "success_url": "http://localhost:5173/?payment_success=1"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Polar access token is not configured."


def test_checkout_upstream_error_returns_502(monkeypatch):
    async def fake_create_checkout_url(*args, **kwargs):
        raise PolarCheckoutUpstreamError('{"error_code":1010,"detail":"Access denied"}', status_code=403)

    monkeypatch.setattr("backend.app.main.billing_service.create_checkout_url", fake_create_checkout_url)
    monkeypatch.setattr("backend.app.main.billing_service.async_get_or_create_db_account", _fake_get_or_create_account)
    app.dependency_overrides[auth_service.get_current_user] = _auth_user
    app.dependency_overrides[get_db] = _fake_db
    try:
        response = TestClient(app).post(
            "/api/billing/checkout",
            json={"product_code": "starter_monthly", "success_url": "http://localhost:5173/?payment_success=1"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502
    assert response.json()["detail"] == "Failed to create the Polar checkout."


def test_checkout_success_returns_url(monkeypatch):
    async def fake_create_checkout_url(*args, **kwargs):
        return "https://polar.sh/checkout/test"

    monkeypatch.setattr("backend.app.main.billing_service.create_checkout_url", fake_create_checkout_url)
    monkeypatch.setattr("backend.app.main.billing_service.async_get_or_create_db_account", _fake_get_or_create_account)
    app.dependency_overrides[auth_service.get_current_user] = _auth_user
    app.dependency_overrides[get_db] = _fake_db
    try:
        response = TestClient(app).post(
            "/api/billing/checkout",
            json={"product_code": "starter_monthly", "success_url": "http://localhost:5173/?payment_success=1"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["checkout_url"] == "https://polar.sh/checkout/test"


def test_checkout_existing_subscriber_returns_customer_portal(monkeypatch):
    async def fake_get_or_create_account(*args, **kwargs):
        return SimpleNamespace(subscription_status="student_plus")

    async def fake_create_customer_portal_url(*args, **kwargs):
        return "https://polar.sh/portal/session"

    async def fail_create_checkout_url(*args, **kwargs):
        raise AssertionError("checkout should not be created for an existing subscriber")

    monkeypatch.setattr("backend.app.main.billing_service.async_get_or_create_db_account", fake_get_or_create_account)
    monkeypatch.setattr("backend.app.main.billing_service.create_customer_portal_url", fake_create_customer_portal_url)
    monkeypatch.setattr("backend.app.main.billing_service.create_checkout_url", fail_create_checkout_url)
    app.dependency_overrides[auth_service.get_current_user] = _auth_user
    app.dependency_overrides[get_db] = _fake_db
    try:
        response = TestClient(app).post(
            "/api/billing/checkout",
            json={"product_code": "pro_monthly", "success_url": "http://localhost:5173/?payment_success=1"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["checkout_url"] == "https://polar.sh/portal/session"
    assert "existing subscription" in response.json()["message"]


def test_free_plan_for_existing_subscriber_returns_customer_portal(monkeypatch):
    async def fake_get_or_create_account(*args, **kwargs):
        return SimpleNamespace(subscription_status="pro")

    async def fake_create_customer_portal_url(*args, **kwargs):
        return "https://polar.sh/portal/cancel"

    async def fail_create_checkout_url(*args, **kwargs):
        raise AssertionError("free plan should use the customer portal")

    monkeypatch.setattr("backend.app.main.billing_service.async_get_or_create_db_account", fake_get_or_create_account)
    monkeypatch.setattr("backend.app.main.billing_service.create_customer_portal_url", fake_create_customer_portal_url)
    monkeypatch.setattr("backend.app.main.billing_service.create_checkout_url", fail_create_checkout_url)
    app.dependency_overrides[auth_service.get_current_user] = _auth_user
    app.dependency_overrides[get_db] = _fake_db
    try:
        response = TestClient(app).post(
            "/api/billing/checkout",
            json={"product_code": "free", "success_url": "http://localhost:5173/"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["checkout_url"] == "https://polar.sh/portal/cancel"


def test_billing_status_syncs_polar_state_for_paid_accounts(monkeypatch):
    calls = {"sync": 0, "load": 0, "commit": 0}

    async def fake_get_or_create_account(*args, **kwargs):
        return SimpleNamespace(subscription_status="student_plus")

    async def fake_sync_from_polar_customer_state(*args, **kwargs):
        calls["sync"] += 1
        return True

    async def fake_load_to_memory(*args, **kwargs):
        calls["load"] += 1

    def fake_get_status(*args, **kwargs):
        return {
            "subscription_status": "pro",
            "credits_remaining": 150000,
            "plan_name": "Pro",
            "monthly_credit_limit": 150000,
            "usage_used": 0,
            "usage_limit": 150000,
            "usage_percent": 0,
            "available_credit_packs": [],
        }

    class FakeStatusDb(FakeDb):
        async def commit(self):
            calls["commit"] += 1

    async def fake_db():
        yield FakeStatusDb()

    monkeypatch.setattr("backend.app.main.billing_service.async_get_or_create_db_account", fake_get_or_create_account)
    monkeypatch.setattr("backend.app.main.billing_service.async_sync_from_polar_customer_state", fake_sync_from_polar_customer_state)
    monkeypatch.setattr("backend.app.main.billing_service.async_load_to_memory", fake_load_to_memory)
    monkeypatch.setattr("backend.app.main.billing_service.get_status", fake_get_status)
    app.dependency_overrides[auth_service.get_current_user] = _auth_user
    app.dependency_overrides[get_db] = fake_db
    try:
        response = TestClient(app).get("/api/billing/status")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["subscription_status"] == "pro"
    assert calls == {"sync": 1, "load": 1, "commit": 1}
