from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID

from fastapi.testclient import TestClient

from backend.app.db.database import get_db
from backend.app.db.models import Profile, UserActivityLogDB
from backend.app.main import app
from backend.app.services import auth as auth_service
from backend.app.services.auth import AuthUser


USER_ID = "00000000-0000-0000-0000-000000000001"


class FakeResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class FakeDb:
    def __init__(self, profile, execute_values=None):
        self.profile = profile
        self.execute_values = list(execute_values or [])
        self.added = []
        self.committed = False
        self.flushed = False

    async def execute(self, _statement):
        if self.execute_values:
            return FakeResult(self.execute_values.pop(0))
        return FakeResult(self.profile)

    def add(self, value):
        self.added.append(value)
        if isinstance(value, Profile):
            self.profile = value

    async def flush(self):
        self.flushed = True

    async def commit(self):
        self.committed = True


def _auth_user() -> AuthUser:
    return AuthUser(user_id=USER_ID, email="student@example.com")


def _override_db(fake_db):
    async def _fake_db():
        yield fake_db

    return _fake_db


def test_delete_account_marks_profile_deleted_and_logs_activity(monkeypatch):
    profile = Profile(id=UUID(USER_ID), email="student@example.com")
    fake_db = FakeDb(profile)

    async def fake_get_or_create_account(*args, **kwargs):
        return SimpleNamespace(
            subscription_status="student_plus",
            plan_name="Student Plus",
            monthly_credit_limit=60000,
            credits_remaining=12000,
            polar_subscription_id="sub_123",
        )

    async def fake_sync_subscription(*args, **kwargs):
        return None

    monkeypatch.setattr("backend.app.main.billing_service.async_get_or_create_db_account", fake_get_or_create_account)
    monkeypatch.setattr("backend.app.main.billing_service.async_sync_subscription", fake_sync_subscription)
    app.dependency_overrides[auth_service.get_current_user] = _auth_user
    app.dependency_overrides[get_db] = _override_db(fake_db)
    try:
        response = TestClient(app).post("/api/auth/delete-account")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["deleted"] is True
    assert profile.deleted_at is not None
    assert fake_db.committed is True
    logs = [item for item in fake_db.added if isinstance(item, UserActivityLogDB)]
    assert len(logs) == 1
    assert logs[0].event_type == "account_deleted"
    assert str(logs[0].user_id) == USER_ID


def test_deleted_account_is_blocked_from_protected_api():
    profile = Profile(
        id=UUID(USER_ID),
        email="student@example.com",
        deleted_at=datetime.now(timezone.utc),
    )
    fake_db = FakeDb(profile)

    app.dependency_overrides[auth_service.get_current_user] = _auth_user
    app.dependency_overrides[get_db] = _override_db(fake_db)
    try:
        response = TestClient(app).get("/api/billing/status")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "This account has been deleted."


def test_complete_onboarding_sets_username_and_acceptance_times():
    profile = Profile(id=UUID(USER_ID), email="student@example.com")
    fake_db = FakeDb(profile, execute_values=[None, profile])

    app.dependency_overrides[auth_service.get_current_user] = _auth_user
    app.dependency_overrides[get_db] = _override_db(fake_db)
    try:
        response = TestClient(app).post(
            "/api/auth/complete-onboarding",
            json={
                "username": "google_student",
                "accepted_terms": True,
                "accepted_privacy": True,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"username": "google_student", "onboarded": True}
    assert profile.username == "google_student"
    assert profile.nickname == "google_student"
    assert profile.terms_accepted_at is not None
    assert profile.privacy_accepted_at is not None
    assert profile.onboarded_at is not None
    assert fake_db.committed is True


def test_complete_onboarding_rejects_taken_username():
    profile = Profile(id=UUID(USER_ID), email="student@example.com")
    taken_profile = Profile(id=UUID("00000000-0000-0000-0000-000000000002"), username="taken")
    fake_db = FakeDb(profile, execute_values=[taken_profile])

    app.dependency_overrides[auth_service.get_current_user] = _auth_user
    app.dependency_overrides[get_db] = _override_db(fake_db)
    try:
        response = TestClient(app).post(
            "/api/auth/complete-onboarding",
            json={
                "username": "taken",
                "accepted_terms": True,
                "accepted_privacy": True,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"] == "Username is already taken."
