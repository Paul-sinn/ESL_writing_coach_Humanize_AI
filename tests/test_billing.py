import pytest
from backend.app.services.billing import BillingService


@pytest.fixture
def service():
    return BillingService()


def test_get_or_create_returns_existing_free(service):
    account = service.get_or_create_account("demo-free")
    assert account.user_id == "demo-free"
    assert account.credits_remaining == 0
    assert account.subscription_status == "free"


def test_get_or_create_new_user_defaults_to_free(service):
    account = service.get_or_create_account("unknown-user-xyz")
    assert account.subscription_status == "free"
    assert account.credits_remaining == 0


def test_get_status_free_user(service):
    status = service.get_status("demo-free")
    assert status.subscription_status == "free"
    assert status.credits_remaining == 0
    assert status.plan_name == "Free"
    assert status.monthly_credit_limit == 0


def test_get_status_pro_user(service):
    status = service.get_status("demo-pro")
    assert status.subscription_status == "pro"
    assert status.credits_remaining == 150000
    assert status.plan_name == "Pro"
    assert status.monthly_credit_limit == 150000


def test_get_status_student_plus(service):
    status = service.get_status("demo-plus")
    assert status.subscription_status == "student_plus"
    assert status.plan_name == "Student Plus"
    assert status.monthly_credit_limit == 60000


def test_get_status_includes_six_checkout_options(service):
    status = service.get_status("demo-free")
    assert len(status.available_credit_packs) == 6


def test_ensure_credits_sufficient(service):
    has_credits, _ = service.ensure_credits("demo-pro", 1000)
    assert has_credits is True


def test_ensure_credits_insufficient(service):
    has_credits, _ = service.ensure_credits("demo-free", 50)
    assert has_credits is False


def test_ensure_credits_exact_match(service):
    service._accounts["demo-pro"].credits_remaining = 50
    has_credits, _ = service.ensure_credits("demo-pro", 50)
    assert has_credits is True


def test_deduct_credits_reduces_balance(service):
    account = service.deduct_credits("demo-pro", 500)
    assert account.credits_remaining == 149500


def test_deduct_zero_credits_is_noop(service):
    account = service.deduct_credits("demo-pro", 0)
    assert account.credits_remaining == 150000


def test_deduct_credits_insufficient_raises(service):
    with pytest.raises(ValueError, match="Insufficient credits"):
        service.deduct_credits("demo-free", 50)


def test_deduct_credits_exact_balance_empties_account(service):
    service._accounts["demo-pro"].credits_remaining = 50
    account = service.deduct_credits("demo-pro", 50)
    assert account.credits_remaining == 0


def test_build_redirect_free_user_offers_upgrade(service):
    redirect = service.build_redirect("demo-free", "Writing Coach")
    assert "Writing Coach" in redirect.message
    assert "Student Plus" in redirect.recommended_offer
    assert redirect.route == "/billing"
    assert len(redirect.checkout_options) > 0


def test_build_redirect_paid_user_offers_credit_pack(service):
    redirect = service.build_redirect("demo-pro", "Full Review")
    assert "Full Review" in redirect.message
    assert "credit pack" in redirect.recommended_offer.lower()


def test_create_checkout_url_contains_product_code(service):
    url = service.create_checkout_url("student_plus_monthly")
    assert "student_plus_monthly" in url
