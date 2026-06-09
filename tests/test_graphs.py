import pytest
from backend.app.graphs import billing_graph, coach_graph, humanize_graph
from backend.app.services.billing import billing_service
from backend.app.services.coaching import coaching_service
from backend.app.services.humanize import humanize_service

_TEXT = "This is a short essay. It sounds polished. Furthermore, it repeats transitions."
_LONG_TEXT = " ".join(["word"] * 310)


# --- coach_graph basic ---

def test_coach_graph_returns_feedback():
    result = coach_graph.invoke({
        "user_id": "demo-free",
        "client_ip": "10.0.0.1",
        "text": _TEXT,
        "assignment_type": "general_academic",
        "writing_level": "intermediate",
        "depth": "basic",
    })
    response = result["response"]
    assert response.input_word_count > 0
    assert response.max_word_limit == 1200
    assert isinstance(response.feedback_items, list)
    assert isinstance(response.strengths, list)


def test_coach_graph_returns_scores():
    result = coach_graph.invoke({
        "user_id": "demo-free",
        "client_ip": "10.0.0.11",
        "text": _TEXT,
        "depth": "basic",
    })
    response = result["response"]
    assert 0 <= response.ai_like_score <= 100
    assert 0 <= response.naturalness_score <= 100
    assert 0 <= response.personal_voice_score <= 100
    assert 0 <= response.clarity_score <= 100
    assert response.verdict_label in ("low", "medium", "high")


def test_coach_graph_korean_input_keeps_feedback_in_english(monkeypatch):
    monkeypatch.setattr(coaching_service, "_client", None)

    result = coach_graph.invoke({
        "user_id": "demo-plus",
        "text": "저는 수업에서 배운 내용을 바탕으로 이 글을 썼습니다. 제 경험도 함께 설명하고 싶습니다.",
        "depth": "deep",
    })
    response = result["response"]
    assert response.feedback_items
    assert any("저는" in item.sentence for item in response.feedback_items)
    user_facing_feedback = " ".join([
        response.overall_summary,
        " ".join(item.explanation for item in response.feedback_items),
        " ".join(item.suggestion for item in response.feedback_items),
        " ".join(item.why_it_matters or "" for item in response.feedback_items),
    ])
    assert "구체적인" not in user_facing_feedback
    assert "설명" not in user_facing_feedback


def test_coach_graph_feedback_items_have_severity():
    result = coach_graph.invoke({
        "user_id": "demo-free",
        "client_ip": "10.0.0.12",
        "text": _TEXT,
        "depth": "basic",
    })
    for item in result["response"].feedback_items:
        assert item.severity in ("low", "medium", "high")


def test_coach_graph_includes_integrity_content():
    result = coach_graph.invoke({
        "user_id": "demo-free",
        "client_ip": "10.0.0.2",
        "text": _TEXT,
        "depth": "basic",
    })
    response = result["response"]
    assert response.integrity_note != ""
    assert response.disclosure_statement != ""


def test_coach_graph_free_user_word_limit():
    result = coach_graph.invoke({
        "user_id": "demo-free",
        "client_ip": "10.0.0.3",
        "text": _LONG_TEXT,
        "depth": "basic",
    })
    response = result["response"]
    assert response.billing_redirect is not None
    assert "300" in response.overall_summary
    assert response.credits_charged == 0


def test_coach_graph_insufficient_credits():
    result = coach_graph.invoke({
        "user_id": "demo-starter",
        "text": _TEXT,
        "depth": "full_review",
    })
    # demo-starter has 20000 credits; short text full_review = 15 words * 5 = 75 credits
    response = result["response"]
    assert response.billing_redirect is None  # 20000 > 75
    assert response.credits_charged > 0


def test_coach_graph_empty_text_raises():
    with pytest.raises(ValueError, match="paste your essay"):
        coach_graph.invoke({
            "user_id": "demo-free",
            "client_ip": "10.0.0.9",
            "text": "   ",
            "depth": "basic",
        })


def test_coach_graph_free_daily_limit():
    payload = {
        "user_id": "demo-free",
        "client_ip": "203.0.113.50",
        "text": _TEXT,
        "depth": "basic",
    }
    first = coach_graph.invoke(payload)["response"]
    second = coach_graph.invoke(payload)["response"]
    third = coach_graph.invoke(payload)["response"]
    assert first.billing_redirect is None
    assert second.billing_redirect is None
    assert third.billing_redirect is not None


def test_coach_graph_deducts_credits_for_paid_user():
    billing_service._accounts["demo-plus"].credits_remaining = 60000
    initial = billing_service._accounts["demo-plus"].credits_remaining
    result = coach_graph.invoke({
        "user_id": "demo-plus",
        "text": _TEXT,
        "depth": "deep",
    })
    response = result["response"]
    assert response.billing_redirect is None
    assert response.credits_charged > 0
    assert billing_service._accounts["demo-plus"].credits_remaining == initial - response.credits_charged


# --- humanize_graph ---

def test_humanize_graph_rewrites_text():
    result = humanize_graph.invoke({
        "user_id": "demo-pro",
        "text": _TEXT,
        "tone": "natural_student",
        "strength": "balanced",
        "preserve_meaning": True,
        "preserve_citations": False,
        "preserve_structure": False,
    })
    response = result["response"]
    assert response.rewritten_text != ""
    assert response.input_word_count > 0
    assert response.rewritten_word_count > 0
    assert response.billing_redirect is None


def test_humanize_graph_deducts_credits():
    billing_service._accounts["demo-plus"].credits_remaining = 60000
    initial = billing_service._accounts["demo-plus"].credits_remaining
    result = humanize_graph.invoke({
        "user_id": "demo-plus",
        "text": _TEXT,
        "tone": "natural_student",
        "strength": "balanced",
        "preserve_meaning": True,
        "preserve_citations": False,
        "preserve_structure": False,
    })
    response = result["response"]
    assert response.billing_redirect is None
    assert response.credits_charged > 0
    assert billing_service._accounts["demo-plus"].credits_remaining == initial - response.credits_charged


def test_humanize_graph_reuses_coach_feedback_without_analysis_call(monkeypatch):
    billing_service._accounts["demo-plus"].credits_remaining = 60000

    def fail_if_called(*args, **kwargs):
        raise AssertionError("analyze_for_rewrite should not run when coach_feedback is provided")

    monkeypatch.setattr(humanize_service, "analyze_for_rewrite", fail_if_called)

    result = humanize_graph.invoke({
        "user_id": "demo-plus",
        "text": _TEXT,
        "tone": "natural_student",
        "strength": "balanced",
        "preserve_meaning": True,
        "preserve_citations": False,
        "preserve_structure": False,
        "coach_feedback": [
            {
                "sentence": "Furthermore, it repeats transitions.",
                "issue_type": "ai_pattern",
                "severity": "medium",
                "explanation": "This transition sounds formulaic.",
                "suggestion": "Use a more direct transition.",
            }
        ],
    })
    response = result["response"]
    assert response.billing_redirect is None
    assert response.credits_charged == 5000


def test_humanize_graph_insufficient_credits():
    result = humanize_graph.invoke({
        "user_id": "demo-free",
        "text": _TEXT,
        "tone": "natural_student",
        "strength": "balanced",
        "preserve_meaning": True,
        "preserve_citations": False,
        "preserve_structure": False,
    })
    response = result["response"]
    assert response.billing_redirect is not None
    assert response.credits_charged == 0


# --- billing_graph ---

def test_billing_graph_returns_redirect_for_free_user():
    result = billing_graph.invoke({"user_id": "demo-free", "trigger_action": "Writing Coach"})
    redirect = result["response"]
    assert redirect.route == "/billing"
    assert len(redirect.checkout_options) > 0
    assert "Writing Coach" in redirect.message


def test_billing_graph_pro_user_offers_credit_pack():
    result = billing_graph.invoke({"user_id": "demo-pro", "trigger_action": "Full Review"})
    redirect = result["response"]
    assert "credit pack" in redirect.recommended_offer.lower()
