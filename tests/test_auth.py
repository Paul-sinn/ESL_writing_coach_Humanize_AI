from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from jose import jwt

from backend.app.config import get_settings
from backend.app.services.auth import (
    _verified_emails,
    create_demo_access_token,
    create_access_token,
    get_current_user,
    hash_password,
    register,
    login,
    verify_password,
    verify_demo_credentials,
)

settings = get_settings()


@pytest.fixture(autouse=True)
def reset_auth_state():
    _verified_emails.clear()
    yield
    _verified_emails.clear()


def _mock_db(user=None):
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    db.execute.return_value = result
    db.flush = AsyncMock()
    db.add = MagicMock()  # synchronous — prevents AsyncMock coroutine warning
    return db


def _mock_user(
    email="user@test.com",
    username="testuser",
    nickname="TestNick",
    password="password123",
):
    user = MagicMock()
    user.id = "00000000-0000-0000-0000-000000000001"
    user.email = email
    user.username = username
    user.nickname = nickname
    user.hashed_password = hash_password(password)
    user.is_active = True
    return user


# ── hash / verify ─────────────────────────────────────────────────────────────

def test_hash_verify_roundtrip():
    hashed = hash_password("mysecret99")
    assert verify_password("mysecret99", hashed)


def test_verify_wrong_password_returns_false():
    hashed = hash_password("correct")
    assert not verify_password("wrong", hashed)


def test_different_hashes_for_same_password():
    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2  # bcrypt salt makes each hash unique


# ── create_access_token ───────────────────────────────────────────────────────

def test_token_contains_expected_claims():
    token = create_access_token({"sub": "uid-123", "email": "a@b.com", "username": "alice"})
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert payload["sub"] == "uid-123"
    assert payload["email"] == "a@b.com"
    assert payload["username"] == "alice"
    assert "exp" in payload


# ── register() ────────────────────────────────────────────────────────────────

def test_register_new_user_returns_jwt():
    db = _mock_db(user=None)
    token = asyncio.run(register("new@test.com", "newuser", "NewNick", "pass1234!", db))
    assert isinstance(token, str)
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert payload["email"] == "new@test.com"
    assert payload["username"] == "newuser"
    assert payload["nickname"] == "NewNick"


def test_register_adds_email_to_verified():
    db = _mock_db(user=None)
    asyncio.run(register("new@test.com", "newuser", "NewNick", "pass1234!", db))
    assert "new@test.com" in _verified_emails


def test_register_duplicate_email_raises_409():
    existing = _mock_user()
    db = _mock_db(user=existing)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(register("user@test.com", "other", "Other", "pass1234!", db))
    assert exc.value.status_code == 409
    assert "Email" in exc.value.detail


def test_register_duplicate_username_raises_409():
    db = AsyncMock()
    db.flush = AsyncMock()
    result_none = MagicMock()
    result_none.scalar_one_or_none.return_value = None
    result_hit = MagicMock()
    result_hit.scalar_one_or_none.return_value = _mock_user()
    # First call = email check (None), second call = username check (hit)
    db.execute.side_effect = [result_none, result_hit]
    with pytest.raises(HTTPException) as exc:
        asyncio.run(register("new@test.com", "takenuser", "Nick", "pass1234!", db))
    assert exc.value.status_code == 409
    assert "Username" in exc.value.detail


# ── login() ───────────────────────────────────────────────────────────────────

def test_login_correct_password_returns_token_and_info():
    user = _mock_user(password="correct123")
    db = _mock_db(user=user)
    token, username, nickname = asyncio.run(login("user@test.com", "correct123", db))
    assert isinstance(token, str)
    assert username == "testuser"
    assert nickname == "TestNick"


def test_login_token_contains_user_fields():
    user = _mock_user(username="alice", nickname="AliceNick", password="pass9999")
    db = _mock_db(user=user)
    token, _, _ = asyncio.run(login("user@test.com", "pass9999", db))
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert payload["username"] == "alice"
    assert payload["nickname"] == "AliceNick"


def test_login_wrong_password_raises_401():
    user = _mock_user(password="correct123")
    db = _mock_db(user=user)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(login("user@test.com", "wrongpass", db))
    assert exc.value.status_code == 401


def test_login_nonexistent_user_raises_401():
    db = _mock_db(user=None)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(login("nobody@test.com", "anypass", db))
    assert exc.value.status_code == 401


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

