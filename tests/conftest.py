import pytest
from backend.app.services.billing import UserAccount, billing_service
from backend.app.services.rate_limits import rate_limit_service

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture(autouse=True)
def reset_services():
    billing_service._accounts = {
        TEST_USER_ID: UserAccount(TEST_USER_ID, "free", 0),
    }
    rate_limit_service._attempts.clear()
    yield
