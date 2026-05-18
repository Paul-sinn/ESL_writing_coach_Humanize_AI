from fastapi.testclient import TestClient

from backend.app.db.database import get_db
from backend.app.main import app
from backend.app.services import auth as auth_service
from backend.app.services.auth import AuthUser


class FailingDb:
    async def execute(self, *args, **kwargs):
        raise AssertionError("Demo users should not use persistent DB billing.")

    async def commit(self):
        raise AssertionError("Demo users should not commit DB billing changes.")

    async def rollback(self):
        raise AssertionError("Demo users should not roll back DB billing changes.")


def _demo_user() -> AuthUser:
    return AuthUser(user_id="demo-plus", email="demo@student.test")


async def _failing_db():
    yield FailingDb()


def test_demo_billing_status_skips_persistent_db():
    app.dependency_overrides[auth_service.get_current_user] = _demo_user
    app.dependency_overrides[get_db] = _failing_db
    try:
        response = TestClient(app).get("/api/billing/status")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["subscription_status"] == "student_plus"


def test_demo_coach_skips_persistent_db():
    app.dependency_overrides[auth_service.get_current_user] = _demo_user
    app.dependency_overrides[get_db] = _failing_db
    try:
        response = TestClient(app).post(
            "/api/coach",
            json={
                "text": "This essay needs clearer examples and a stronger personal voice.",
                "assignment_type": "general_academic",
                "writing_level": "intermediate",
                "depth": "basic",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "overall_summary" in response.json()
