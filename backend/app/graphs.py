from __future__ import annotations

from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph

from .config import get_settings
from .schemas import CoachResponse, FeedbackItem, RewriterResponse
from .services.billing import billing_service
from .services.coaching import coaching_service
from .services.rewriter import rewriter_service
from .services.rate_limits import rate_limit_service
from .utils.text import count_words


settings = get_settings()


def verdict_from_score(score: int) -> Literal["low", "medium", "high"]:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


class CoachState(TypedDict, total=False):
    user_id: str
    text: str
    assignment_type: str
    writing_level: str
    depth: str
    input_word_count: int
    subscription_status: str
    credits_remaining: int
    credits_required: int
    credits_reserved: bool
    selected_model: str
    feedback_items: list[dict]
    strengths: list[str]
    overall_summary: str
    ai_like_score: int
    naturalness_score: int
    personal_voice_score: int
    clarity_score: int
    verdict_label: str
    signals: list[str]
    integrity_note: str
    disclosure_statement: str
    billing_redirect: Any
    error: str | None
    response: CoachResponse


class RewriterState(TypedDict, total=False):
    user_id: str
    text: str
    tone: str
    strength: str
    persona: str
    coach_feedback: list[dict] | None
    preserve_meaning: bool
    preserve_citations: bool
    preserve_structure: bool
    input_word_count: int
    subscription_status: str
    credits_remaining: int
    credits_required: int
    credits_reserved: bool
    analysis_result: dict
    rewritten_text: str
    rewritten_word_count: int
    summary_of_changes: str
    key_improvements: list[str]
    billing_redirect: Any
    error: str | None
    response: RewriterResponse


class BillingState(TypedDict, total=False):
    user_id: str
    subscription_status: str
    credits_remaining: int
    trigger_action: str
    recommended_offer: str
    checkout_options: Any
    portal_url: str | None
    error: str | None
    response: Any


# ── Shared ───────────────────────────────────────────────────────────────────

def load_user_context(state: CoachState | RewriterState) -> dict[str, Any]:
    status = billing_service.get_status(state["user_id"])
    return {
        "subscription_status": status.subscription_status,
        "credits_remaining": status.credits_remaining,
    }


def calculate_coach_credits(word_count: int, depth: str) -> int:
    if depth == "basic":
        return max(
            word_count * settings.basic_coaching_cost_per_word,
            settings.basic_coaching_min_credits,
        )
    if depth == "deep":
        return max(
            word_count * settings.deep_coaching_cost_per_word,
            settings.deep_coaching_min_credits,
        )
    return max(
        word_count * settings.full_review_cost_per_word,
        settings.full_review_min_credits,
    )




def calculate_rewriter_credits(word_count: int) -> int:
    return max(word_count * settings.rewriter_cost_per_word, settings.rewriter_min_credits)


# ── Coach graph nodes ─────────────────────────────────────────────────────────

def validate_coach_input(state: CoachState) -> dict[str, Any]:
    text = state["text"].strip()
    word_count = count_words(text)
    if not text:
        return {"error": "Please paste your essay before requesting feedback."}
    if word_count > settings.max_word_limit:
        return {"error": f"Text must be {settings.max_word_limit} words or fewer."}
    if state.get("subscription_status") == "free" and word_count > settings.free_word_limit:
        return {
            "input_word_count": word_count,
            "billing_redirect": billing_service.build_redirect(state["user_id"], "Writing Coach"),
            "error": "FREE_WORD_LIMIT",
        }
    return {"text": text, "input_word_count": word_count}


def resolve_coach_cost(state: CoachState) -> dict[str, Any]:
    word_count = state["input_word_count"]
    depth = state.get("depth", "deep")
    if depth == "basic":
        credits_required = calculate_coach_credits(word_count, depth)
        model = settings.coach_model
    elif depth == "deep":
        credits_required = calculate_coach_credits(word_count, depth)
        model = settings.coach_model
    else:
        credits_required = calculate_coach_credits(word_count, depth)
        model = settings.advanced_coach_model
    return {"credits_required": credits_required, "selected_model": model}


def check_coach_entitlement(state: CoachState) -> dict[str, Any]:
    if state.get("credits_reserved"):
        return {}
    if state.get("subscription_status") == "free":
        decision = rate_limit_service.check_and_record(state["user_id"])
        if not decision.allowed:
            return {
                "billing_redirect": billing_service.build_redirect(state["user_id"], "Writing Coach"),
                "error": "FREE_LIMIT_REACHED",
            }
        return {}
    has_credits, _ = billing_service.ensure_credits(state["user_id"], state["credits_required"])
    if not has_credits:
        return {
            "billing_redirect": billing_service.build_redirect(state["user_id"], "Writing Coach"),
            "error": "INSUFFICIENT_CREDITS",
        }
    return {}


def run_coaching_analysis(state: CoachState) -> dict[str, Any]:
    result = coaching_service.analyze_and_coach(
        state["text"],
        state.get("assignment_type", "general_academic"),
        state.get("writing_level", "intermediate"),
        state.get("depth", "deep"),
        state["selected_model"],
    )
    ai_like_score = int(result.get("ai_like_score", 50))
    return {
        "feedback_items": result.get("feedback_items", []),
        "strengths": result.get("strengths", []),
        "overall_summary": result.get("overall_summary", ""),
        "ai_like_score": ai_like_score,
        "naturalness_score": int(result.get("naturalness_score", 50)),
        "personal_voice_score": int(result.get("personal_voice_score", 50)),
        "clarity_score": int(result.get("clarity_score", 50)),
        "verdict_label": verdict_from_score(ai_like_score),
        "signals": result.get("signals", []),
    }


def run_academic_integrity(state: CoachState) -> dict[str, Any]:
    result = coaching_service.generate_integrity_content()
    return {
        "integrity_note": result["integrity_note"],
        "disclosure_statement": result["disclosure_statement"],
    }


def deduct_coach_credits(state: CoachState) -> dict[str, Any]:
    if state.get("credits_reserved"):
        return {}
    if state.get("subscription_status") == "free" or state.get("credits_required", 0) <= 0:
        return {}
    account = billing_service.deduct_credits(state["user_id"], state["credits_required"])
    return {"credits_remaining": account.credits_remaining}


def route_to_billing(state: CoachState) -> dict[str, Any]:
    return {}


def format_coach_response(state: CoachState) -> dict[str, Any]:
    error = state.get("error")
    allowed_errors = {"INSUFFICIENT_CREDITS", "FREE_LIMIT_REACHED", "FREE_WORD_LIMIT"}
    if error and error not in allowed_errors:
        raise ValueError(error)

    if error == "FREE_LIMIT_REACHED":
        summary = "You've used your free daily coaching session. Upgrade to continue."
    elif error == "FREE_WORD_LIMIT":
        summary = f"Free plan supports up to {settings.free_word_limit} words. Upgrade to analyze longer essays."
    elif error == "INSUFFICIENT_CREDITS":
        summary = "You need more credits to use this feature."
    else:
        summary = state.get("overall_summary", "")

    is_blocked = bool(state.get("billing_redirect"))
    feedback_items = [] if is_blocked else [FeedbackItem(**item) for item in state.get("feedback_items", [])]

    response = CoachResponse(
        feedback_items=feedback_items,
        strengths=[] if is_blocked else state.get("strengths", []),
        overall_summary=summary,
        ai_like_score=state.get("ai_like_score", 0),
        naturalness_score=state.get("naturalness_score", 0),
        personal_voice_score=state.get("personal_voice_score", 0),
        clarity_score=state.get("clarity_score", 0),
        verdict_label=state.get("verdict_label", "low"),
        signals=state.get("signals", []),
        integrity_note=state.get("integrity_note", ""),
        disclosure_statement=state.get("disclosure_statement", ""),
        credits_charged=0 if is_blocked else state.get("credits_required", 0),
        credits_remaining=state.get("credits_remaining", 0),
        input_word_count=state.get("input_word_count", 0),
        max_word_limit=settings.max_word_limit,
        billing_redirect=state.get("billing_redirect"),
    )
    return {"response": response}


def validation_should_continue(state: CoachState) -> str:
    return "error" if state.get("error") else "continue"


def entitlement_should_continue(state: CoachState) -> str:
    if state.get("error") in {"INSUFFICIENT_CREDITS", "FREE_LIMIT_REACHED"}:
        return "billing"
    if state.get("error"):
        return "error"
    return "continue"


# ── Rewriter graph nodes ──────────────────────────────────────────────────────

def validate_rewriter_input(state: RewriterState) -> dict[str, Any]:
    text = state["text"].strip()
    word_count = count_words(text)
    if not text:
        return {"error": "Please paste your essay before rewriting."}
    if word_count > settings.max_word_limit:
        return {"error": f"Text must be {settings.max_word_limit} words or fewer."}
    return {"text": text, "input_word_count": word_count}


def resolve_rewriter_cost(state: RewriterState) -> dict[str, Any]:
    return {"credits_required": calculate_rewriter_credits(state["input_word_count"])}


def check_rewriter_entitlement(state: RewriterState) -> dict[str, Any]:
    if state.get("credits_reserved"):
        return {}
    has_credits, _ = billing_service.ensure_credits(state["user_id"], state["credits_required"])
    if not has_credits:
        return {
            "billing_redirect": billing_service.build_redirect(state["user_id"], "Rewriter"),
            "error": "INSUFFICIENT_CREDITS",
        }
    return {}


def run_rewriter_analysis(state: RewriterState) -> dict[str, Any]:
    coach_feedback = state.get("coach_feedback")
    if coach_feedback:
        patterns = [item["sentence"] for item in coach_feedback
                    if item.get("issue_type") in ("ai_pattern", "robotic_tone")]
        targets = [item["sentence"] for item in coach_feedback
                   if item.get("severity") in ("high", "medium")]
        tone_issues = [item["explanation"] for item in coach_feedback
                       if item.get("issue_type") == "robotic_tone"]
        return {"analysis_result": {
            "patterns_found": patterns[:5],
            "rewrite_targets": targets[:5],
            "tone_issues": tone_issues[:3],
        }}
    result = rewriter_service.analyze_for_rewrite(
        state["text"],
        state.get("tone", "natural_student"),
        state.get("strength", "balanced"),
        settings.coach_model,
    )
    return {"analysis_result": result}


def run_rewriter_rewrite(state: RewriterState) -> dict[str, Any]:
    result = rewriter_service.rewrite(
        state["text"],
        tone=state.get("tone", "natural_student"),
        strength=state.get("strength", "balanced"),
        persona=state.get("persona", "esl_student"),
        preserve_meaning=state.get("preserve_meaning", True),
        preserve_citations=state.get("preserve_citations", False),
        preserve_structure=state.get("preserve_structure", False),
        model=settings.coach_model,
        analysis=state.get("analysis_result"),
    )
    rewritten = result.get("rewritten_text", state["text"])
    return {
        "rewritten_text": rewritten,
        "rewritten_word_count": count_words(rewritten),
        "summary_of_changes": result.get("summary_of_changes", ""),
        "key_improvements": result.get("key_improvements", []),
    }


def deduct_rewriter_credits(state: RewriterState) -> dict[str, Any]:
    if state.get("credits_reserved"):
        return {}
    account = billing_service.deduct_credits(state["user_id"], state["credits_required"])
    return {"credits_remaining": account.credits_remaining}


def route_to_billing_rewriter(state: RewriterState) -> dict[str, Any]:
    return {}


def format_rewriter_response(state: RewriterState) -> dict[str, Any]:
    error = state.get("error")
    if error and error != "INSUFFICIENT_CREDITS":
        raise ValueError(error)

    response = RewriterResponse(
        rewritten_text=state.get("rewritten_text", ""),
        summary_of_changes=state.get("summary_of_changes", "Add credits to unlock Rewriter."),
        key_improvements=state.get("key_improvements", []),
        credits_charged=0 if state.get("billing_redirect") else state.get("credits_required", 0),
        credits_remaining=state.get("credits_remaining", 0),
        input_word_count=state.get("input_word_count", 0),
        rewritten_word_count=state.get("rewritten_word_count", 0),
        billing_redirect=state.get("billing_redirect"),
    )
    return {"response": response}


def rewriter_validation_should_continue(state: RewriterState) -> str:
    return "error" if state.get("error") else "continue"


def rewriter_entitlement_should_continue(state: RewriterState) -> str:
    if state.get("error") == "INSUFFICIENT_CREDITS":
        return "billing"
    if state.get("error"):
        return "error"
    return "continue"


# ── Billing graph nodes ───────────────────────────────────────────────────────

def load_billing_context(state: BillingState) -> dict[str, Any]:
    status = billing_service.get_status(state["user_id"])
    return {
        "subscription_status": status.subscription_status,
        "credits_remaining": status.credits_remaining,
    }


def resolve_billing_offer(state: BillingState) -> dict[str, Any]:
    if state["subscription_status"] == "free":
        offer = "Upgrade to Student Plus"
    else:
        offer = "Buy a credit pack"
    return {"recommended_offer": offer}


def build_checkout_options(state: BillingState) -> dict[str, Any]:
    redirect = billing_service.build_redirect(state["user_id"], state["trigger_action"])
    return {"checkout_options": redirect.checkout_options, "portal_url": redirect.route}


def format_billing_redirect(state: BillingState) -> dict[str, Any]:
    return {"response": billing_service.build_redirect(state["user_id"], state["trigger_action"])}


# ── Graph builders ────────────────────────────────────────────────────────────

def build_coach_graph():
    graph = StateGraph(CoachState)
    graph.add_node("load_user_context", load_user_context)
    graph.add_node("validate_coach_input", validate_coach_input)
    graph.add_node("resolve_coach_cost", resolve_coach_cost)
    graph.add_node("check_coach_entitlement", check_coach_entitlement)
    graph.add_node("run_coaching_analysis", run_coaching_analysis)
    graph.add_node("run_academic_integrity", run_academic_integrity)
    graph.add_node("deduct_coach_credits", deduct_coach_credits)
    graph.add_node("route_to_billing", route_to_billing)
    graph.add_node("format_coach_response", format_coach_response)

    graph.set_entry_point("load_user_context")
    graph.add_edge("load_user_context", "validate_coach_input")
    graph.add_conditional_edges(
        "validate_coach_input",
        validation_should_continue,
        {"continue": "resolve_coach_cost", "error": "format_coach_response"},
    )
    graph.add_edge("resolve_coach_cost", "check_coach_entitlement")
    graph.add_conditional_edges(
        "check_coach_entitlement",
        entitlement_should_continue,
        {"continue": "run_coaching_analysis", "billing": "route_to_billing", "error": "format_coach_response"},
    )
    graph.add_edge("run_coaching_analysis", "run_academic_integrity")
    graph.add_edge("run_academic_integrity", "deduct_coach_credits")
    graph.add_edge("deduct_coach_credits", "format_coach_response")
    graph.add_edge("route_to_billing", "format_coach_response")
    graph.add_edge("format_coach_response", END)
    return graph.compile()


def build_rewriter_graph():
    graph = StateGraph(RewriterState)
    graph.add_node("load_user_context", load_user_context)
    graph.add_node("validate_rewriter_input", validate_rewriter_input)
    graph.add_node("resolve_rewriter_cost", resolve_rewriter_cost)
    graph.add_node("check_rewriter_entitlement", check_rewriter_entitlement)
    graph.add_node("run_rewriter_analysis", run_rewriter_analysis)
    graph.add_node("run_rewriter_rewrite", run_rewriter_rewrite)
    graph.add_node("deduct_rewriter_credits", deduct_rewriter_credits)
    graph.add_node("route_to_billing_rewriter", route_to_billing_rewriter)
    graph.add_node("format_rewriter_response", format_rewriter_response)

    graph.set_entry_point("load_user_context")
    graph.add_edge("load_user_context", "validate_rewriter_input")
    graph.add_conditional_edges(
        "validate_rewriter_input",
        rewriter_validation_should_continue,
        {"continue": "resolve_rewriter_cost", "error": "format_rewriter_response"},
    )
    graph.add_edge("resolve_rewriter_cost", "check_rewriter_entitlement")
    graph.add_conditional_edges(
        "check_rewriter_entitlement",
        rewriter_entitlement_should_continue,
        {"continue": "run_rewriter_analysis", "billing": "route_to_billing_rewriter", "error": "format_rewriter_response"},
    )
    graph.add_edge("run_rewriter_analysis", "run_rewriter_rewrite")
    graph.add_edge("run_rewriter_rewrite", "deduct_rewriter_credits")
    graph.add_edge("deduct_rewriter_credits", "format_rewriter_response")
    graph.add_edge("route_to_billing_rewriter", "format_rewriter_response")
    graph.add_edge("format_rewriter_response", END)
    return graph.compile()


def build_billing_graph():
    graph = StateGraph(BillingState)
    graph.add_node("load_billing_context", load_billing_context)
    graph.add_node("resolve_billing_offer", resolve_billing_offer)
    graph.add_node("build_checkout_options", build_checkout_options)
    graph.add_node("format_billing_redirect", format_billing_redirect)
    graph.set_entry_point("load_billing_context")
    graph.add_edge("load_billing_context", "resolve_billing_offer")
    graph.add_edge("resolve_billing_offer", "build_checkout_options")
    graph.add_edge("build_checkout_options", "format_billing_redirect")
    graph.add_edge("format_billing_redirect", END)
    return graph.compile()


coach_graph = build_coach_graph()
rewriter_graph = build_rewriter_graph()
billing_graph = build_billing_graph()
