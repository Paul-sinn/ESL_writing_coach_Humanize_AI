from fastapi.testclient import TestClient

from backend.app.db.database import get_db
from backend.app.main import app
from backend.app.services import auth as auth_service
from backend.app.services.auth import AuthUser
from backend.app.services.billing import PolarCheckoutConfigError, PolarCheckoutUpstreamError


class FakeDb:
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
    return object()


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
    assert response.json()["detail"] == "Polar checkout 생성에 실패했습니다."


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
