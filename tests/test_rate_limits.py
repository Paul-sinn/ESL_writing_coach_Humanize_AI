import pytest
from backend.app.services.rate_limits import DailyBasicAnalysisLimiter


@pytest.fixture
def limiter():
    return DailyBasicAnalysisLimiter(daily_limit=2)


def test_first_attempt_allowed(limiter):
    decision = limiter.check_and_record("1.2.3.4")
    assert decision.allowed is True
    assert decision.attempts_used == 1
    assert decision.daily_limit == 2


def test_second_attempt_allowed(limiter):
    limiter.check_and_record("1.2.3.4")
    decision = limiter.check_and_record("1.2.3.4")
    assert decision.allowed is True
    assert decision.attempts_used == 2


def test_third_attempt_denied(limiter):
    limiter.check_and_record("1.2.3.4")
    limiter.check_and_record("1.2.3.4")
    decision = limiter.check_and_record("1.2.3.4")
    assert decision.allowed is False
    assert decision.attempts_used == 2


def test_different_ips_are_independent(limiter):
    limiter.check_and_record("1.1.1.1")
    limiter.check_and_record("1.1.1.1")
    decision = limiter.check_and_record("2.2.2.2")
    assert decision.allowed is True


def test_blocked_ip_stays_at_limit(limiter):
    for _ in range(5):
        limiter.check_and_record("1.2.3.4")
    decision = limiter.check_and_record("1.2.3.4")
    assert decision.allowed is False
    assert decision.attempts_used == 2
