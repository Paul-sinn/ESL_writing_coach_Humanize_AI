import pytest
from backend.app.services.billing import UserAccount, billing_service
from backend.app.services.rate_limits import rate_limit_service


@pytest.fixture(autouse=True)
def reset_services():
    billing_service._accounts = {
        "demo-free": UserAccount("demo-free", "free", 0),
        "demo-starter": UserAccount("demo-starter", "starter", 20000),
        "demo-plus": UserAccount("demo-plus", "student_plus", 60000),
        "demo-pro": UserAccount("demo-pro", "pro", 150000),
    }
    rate_limit_service._attempts.clear()
    yield
