from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

from jose import jwt

from backend.app.config import get_settings
from backend.app.services.auth import (
    create_demo_access_token,
    create_access_token,
    get_current_user,
    verify_demo_credentials,
)

settings = get_settings()


# ── create_access_token ───────────────────────────────────────────────────────

def test_token_contains_expected_claims():
    token = create_access_token({"sub": "uid-123", "email": "a@b.com", "username": "alice"})
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert payload["sub"] == "uid-123"
    assert payload["email"] == "a@b.com"
    assert payload["username"] == "alice"
    assert "exp" in payload


def test_demo_credentials_disabled_by_default(monkeypatch):
    monkeypatch.setattr("backend.app.services.auth.settings.demo_login_enabled", False)

    assert not verify_demo_credentials("demo@student.test", "demo1234")


def test_demo_credentials_match_when_enabled(monkeypatch):
    monkeypatch.setattr("backend.app.services.auth.settings.demo_login_enabled", True)
    monkeypatch.setattr("backend.app.services.auth.settings.demo_login_email", "demo@student.test")
    monkeypatch.setattr("backend.app.services.auth.settings.demo_login_password", "demo1234")

    assert verify_demo_credentials("DEMO@student.test", "demo1234")
    assert not verify_demo_credentials("demo@student.test", "wrong")


def test_demo_token_authenticates_when_enabled(monkeypatch):
    monkeypatch.setattr("backend.app.services.auth.settings.demo_login_enabled", True)
    monkeypatch.setattr("backend.app.services.auth.settings.demo_login_user_id", "demo-plus")

    token = create_demo_access_token("demo@student.test")
    user = asyncio.run(get_current_user(credentials=MagicMock(credentials=token)))

    assert user.user_id == "demo-plus"
    assert user.email == "demo@student.test"
