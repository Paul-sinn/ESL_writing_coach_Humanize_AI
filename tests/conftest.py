import pytest
import os
from backend.app.services.billing import UserAccount, billing_service
from backend.app.services.rate_limits import rate_limit_service

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_ENCRYPTION_KEY = "00" * 32
TEST_HASH_KEY = "11" * 32


@pytest.fixture(autouse=True)
def reset_services():
    os.environ["ENCRYPTION_KEY"] = TEST_ENCRYPTION_KEY
    os.environ["HASH_KEY"] = TEST_HASH_KEY
    billing_service._accounts = {
        TEST_USER_ID: UserAccount(TEST_USER_ID, "free", 0),
        "demo-free": UserAccount("demo-free", "free", 0),
        "demo-starter": UserAccount("demo-starter", "starter", 20000),
        "demo-plus": UserAccount("demo-plus", "student_plus", 60000),
        "demo-pro": UserAccount("demo-pro", "pro", 150000),
    }
    rate_limit_service._attempts.clear()
    yield
