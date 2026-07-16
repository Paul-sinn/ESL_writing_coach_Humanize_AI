import asyncio
from types import SimpleNamespace

import httpx
import pytest
from backend.app.services.billing import (
    BillingService,
    PolarCheckoutConfigError,
    PolarCheckoutUpstreamError,
    _is_safe_customer_email,
    _polar_api_url,
)


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
    assert status.usage_limit == 60000
    assert status.usage_percent == 0


def test_get_status_reports_monthly_usage_from_remaining_credits(service):
    service._accounts["demo-plus"].credits_remaining = 30000
    status = service.get_status("demo-plus")
    assert status.usage_used == 30000
    assert status.usage_limit == 60000
    assert status.usage_percent == 50


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


def test_create_checkout_url_calls_polar(monkeypatch, service):
    captured = {}

    class FakeResponse:
        status_code = 200
        text = '{"url":"https://polar.sh/checkout/test"}'

        def json(self):
            return {"url": "https://polar.sh/checkout/test"}

    class FakeAsyncClient:
        def __init__(self, timeout):
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json, headers):
            captured["url"] = url
            captured["headers"] = headers
            captured["body"] = json
            return FakeResponse()

    monkeypatch.setattr("backend.app.services.billing.settings.polar_access_token", "polar-token")
    monkeypatch.setattr("backend.app.services.billing.settings.polar_api_base_url", "https://api.polar.sh")
    monkeypatch.setattr("backend.app.services.billing.settings.polar_product_id_student_plus", "product-plus")
    monkeypatch.setattr("backend.app.services.billing.httpx.AsyncClient", FakeAsyncClient)

    url = asyncio.run(
        service.create_checkout_url(
            "student_plus_monthly",
            customer_email="student@gmail.com",
            user_id="00000000-0000-0000-0000-000000000001",
            success_url="http://localhost:5173/?payment_success=1",
        )
    )

    assert url == "https://polar.sh/checkout/test"
    assert captured["url"] == "https://api.polar.sh/v1/checkouts/"
    assert captured["headers"]["User-Agent"] == "pj-1-rewriter-app/0.1 server-checkout"
    assert captured["body"] == {
        "products": ["product-plus"],
        "success_url": "http://localhost:5173/?payment_success=1",
        "customer_email": "student@gmail.com",
        "external_customer_id": "00000000-0000-0000-0000-000000000001",
        "metadata": {"user_id": "00000000-0000-0000-0000-000000000001"},
    }


def test_polar_api_url_accepts_base_with_version(monkeypatch):
    monkeypatch.setattr("backend.app.services.billing.settings.polar_api_base_url", "https://sandbox-api.polar.sh/v1")

    assert _polar_api_url("/checkouts/") == "https://sandbox-api.polar.sh/v1/checkouts/"


def test_create_customer_portal_url_calls_polar(monkeypatch, service):
    captured = {}

    class FakeResponse:
        status_code = 201
        text = "{}"

        def json(self):
            return {"customer_portal_url": "https://polar.sh/portal/session"}

    class FakeAsyncClient:
        def __init__(self, timeout):
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json, headers):
            captured["url"] = url
            captured["body"] = json
            captured["headers"] = headers
            return FakeResponse()

    monkeypatch.setattr("backend.app.services.billing.settings.polar_access_token", "polar-token")
    monkeypatch.setattr("backend.app.services.billing.settings.polar_api_base_url", "https://sandbox-api.polar.sh/v1")
    monkeypatch.setattr("backend.app.services.billing.httpx.AsyncClient", FakeAsyncClient)

    url = asyncio.run(
        service.create_customer_portal_url(
            "00000000-0000-0000-0000-000000000001",
            return_url="https://app.example.test/billing",
        )
    )

    assert url == "https://polar.sh/portal/session"
    assert captured["url"] == "https://sandbox-api.polar.sh/v1/customer-sessions/"
    assert captured["body"] == {
        "external_customer_id": "00000000-0000-0000-0000-000000000001",
        "return_url": "https://app.example.test/billing",
    }
    assert captured["headers"]["User-Agent"] == "pj-1-rewriter-app/0.1 customer-portal"


def test_create_checkout_url_omits_reserved_demo_email(monkeypatch, service):
    captured = {}

    class FakeResponse:
        status_code = 201
        text = "{}"

        def json(self):
            return {"url": "https://polar.sh/checkout/test"}

    class FakeAsyncClient:
        def __init__(self, timeout):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json, headers):
            captured["body"] = json
            return FakeResponse()

    monkeypatch.setattr("backend.app.services.billing.settings.polar_access_token", "polar-token")
    monkeypatch.setattr("backend.app.services.billing.settings.polar_product_id_student_plus", "product-plus")
    monkeypatch.setattr("backend.app.services.billing.httpx.AsyncClient", FakeAsyncClient)

    asyncio.run(
        service.create_checkout_url(
            "student_plus_monthly",
            customer_email="demo@student.test",
            user_id="demo-plus",
        )
    )

    assert "customer_email" not in captured["body"]
    assert captured["body"]["external_customer_id"] == "demo-plus"


def test_reserved_email_domains_are_not_sent_to_polar():
    assert _is_safe_customer_email("student@gmail.com")
    assert not _is_safe_customer_email("demo@student.test")
    assert not _is_safe_customer_email("demo@example.com")
    assert not _is_safe_customer_email("not-an-email")


def test_create_checkout_url_rejects_unsupported_product(service):
    with pytest.raises(PolarCheckoutConfigError, match="Unsupported product code"):
        asyncio.run(service.create_checkout_url("not-a-real-product"))


def test_create_checkout_url_rejects_missing_polar_product_id(monkeypatch, service):
    monkeypatch.setattr("backend.app.services.billing.settings.polar_access_token", "polar-token")
    monkeypatch.setattr("backend.app.services.billing.settings.polar_product_id_credit_m", "")

    with pytest.raises(PolarCheckoutConfigError, match="Polar product ID is not configured for credit_pack_m"):
        asyncio.run(service.create_checkout_url("credit_pack_m"))


def test_create_checkout_url_rejects_missing_polar_access_token(monkeypatch, service):
    monkeypatch.setattr("backend.app.services.billing.settings.polar_access_token", "")
    monkeypatch.setattr("backend.app.services.billing.settings.polar_product_id_pro", "product-pro")

    with pytest.raises(PolarCheckoutConfigError, match="Polar access token is not configured"):
        asyncio.run(service.create_checkout_url("pro_monthly"))


def test_create_checkout_url_surfaces_polar_http_error_response(monkeypatch, service):
    class FakeResponse:
        status_code = 403
        text = '{"error_code":1010,"detail":"Access denied"}'

    class FakeAsyncClient:
        def __init__(self, timeout):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json, headers):
            return FakeResponse()

    monkeypatch.setattr("backend.app.services.billing.settings.polar_access_token", "polar-token")
    monkeypatch.setattr("backend.app.services.billing.settings.polar_api_base_url", "https://api.polar.sh")
    monkeypatch.setattr("backend.app.services.billing.settings.polar_product_id_starter", "product-starter")
    monkeypatch.setattr("backend.app.services.billing.httpx.AsyncClient", FakeAsyncClient)

    with pytest.raises(PolarCheckoutUpstreamError) as exc:
        asyncio.run(service.create_checkout_url("starter_monthly"))
    assert exc.value.status_code == 403
    assert "1010" in exc.value.detail


def test_create_checkout_url_surfaces_polar_network_error(monkeypatch, service):
    class FakeAsyncClient:
        def __init__(self, timeout):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json, headers):
            request = httpx.Request("POST", url)
            raise httpx.RequestError("connection refused", request=request)

    monkeypatch.setattr("backend.app.services.billing.settings.polar_access_token", "polar-token")
    monkeypatch.setattr("backend.app.services.billing.settings.polar_api_base_url", "https://api.polar.sh")
    monkeypatch.setattr("backend.app.services.billing.settings.polar_product_id_credit_s", "product-credit-s")
    monkeypatch.setattr("backend.app.services.billing.httpx.AsyncClient", FakeAsyncClient)

    with pytest.raises(PolarCheckoutUpstreamError, match="connection refused"):
        asyncio.run(service.create_checkout_url("credit_pack_s"))


def test_customer_state_sync_does_not_downgrade_paid_account_without_match(monkeypatch, service):
    account = SimpleNamespace(
        user_id="00000000-0000-0000-0000-000000000001",
        subscription_status="student_plus",
        credits_remaining=42000,
        plan_name="Student Plus",
        monthly_credit_limit=60000,
        polar_subscription_id="sub_existing",
    )
    subscription = SimpleNamespace()

    class FakeResult:
        def __init__(self, value):
            self.value = value

        def scalar_one_or_none(self):
            return self.value

    class FakeDb:
        def __init__(self):
            self.values = [account, subscription]

        async def execute(self, _statement):
            return FakeResult(self.values.pop(0))

    class FakeResponse:
        status_code = 200
        text = '{"active_subscriptions":[]}'

        def json(self):
            return {"active_subscriptions": []}

    class FakeAsyncClient:
        def __init__(self, timeout):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers):
            return FakeResponse()

    monkeypatch.setattr("backend.app.services.billing.settings.polar_access_token", "polar-token")
    monkeypatch.setattr("backend.app.services.billing.httpx.AsyncClient", FakeAsyncClient)

    synced = asyncio.run(
        service.async_sync_from_polar_customer_state(
            "00000000-0000-0000-0000-000000000001",
            FakeDb(),
        )
    )

    assert synced is False
    assert account.subscription_status == "student_plus"
    assert account.plan_name == "Student Plus"
    assert account.monthly_credit_limit == 60000
    assert account.polar_subscription_id == "sub_existing"
