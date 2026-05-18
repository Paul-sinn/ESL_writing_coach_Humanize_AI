from fastapi.testclient import TestClient

from backend.app.main import app


def test_demo_login_disabled_returns_401(monkeypatch):
    monkeypatch.setattr("backend.app.services.auth.settings.demo_login_enabled", False)

    response = TestClient(app).post(
        "/api/auth/demo-login",
        json={"email": "demo@student.test", "password": "demo1234"},
    )

    assert response.status_code == 401


def test_demo_login_returns_token_when_enabled(monkeypatch):
    monkeypatch.setattr("backend.app.services.auth.settings.demo_login_enabled", True)
    monkeypatch.setattr("backend.app.services.auth.settings.demo_login_email", "demo@student.test")
    monkeypatch.setattr("backend.app.services.auth.settings.demo_login_password", "demo1234")
    monkeypatch.setattr("backend.app.services.auth.settings.demo_login_user_id", "demo-plus")

    response = TestClient(app).post(
        "/api/auth/demo-login",
        json={"email": "demo@student.test", "password": "demo1234"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["token_type"] == "bearer"
    assert data["user_id"] == "demo-plus"
