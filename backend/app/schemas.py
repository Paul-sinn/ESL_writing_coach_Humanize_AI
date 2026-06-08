from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .config import get_settings
from .utils.text import count_words


settings = get_settings()
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,50}$")

AssignmentType = Literal[
    "discussion_post",
    "reflection_essay",
    "research_essay",
    "personal_statement",
    "general_academic",
]
WritingLevel = Literal["esl_beginner", "intermediate", "advanced"]
CoachDepth = Literal["basic", "deep", "full_review"]


class CoachRequest(BaseModel):
    text: str = Field(min_length=1)
    assignment_type: AssignmentType = "general_academic"
    writing_level: WritingLevel = "intermediate"
    depth: CoachDepth = "deep"

    @field_validator("text")
    @classmethod
    def validate_word_limit(cls, value: str) -> str:
        if count_words(value) > settings.max_word_limit:
            raise ValueError(f"Text must be {settings.max_word_limit} words or fewer.")
        return value


class FeedbackItem(BaseModel):
    sentence: str
    issue_type: str
    severity: Literal["low", "medium", "high"] = "medium"
    explanation: str
    suggestion: str
    suggested_revision: str | None = None
    why_it_matters: str | None = None


class CheckoutOption(BaseModel):
    code: str
    label: str
    price_usd: int
    credits: int | None = None
    description: str


class BillingRedirect(BaseModel):
    route: str
    message: str
    recommended_offer: str
    checkout_options: list[CheckoutOption]


class CoachResponse(BaseModel):
    feedback_items: list[FeedbackItem]
    strengths: list[str]
    overall_summary: str
    ai_like_score: int = 0
    naturalness_score: int = 0
    personal_voice_score: int = 0
    clarity_score: int = 0
    verdict_label: Literal["low", "medium", "high"] = "low"
    signals: list[str] = Field(default_factory=list)
    integrity_note: str
    disclosure_statement: str
    credits_charged: int
    credits_remaining: int
    input_word_count: int
    max_word_limit: int
    billing_redirect: BillingRedirect | None = None


class HumanizeRequest(BaseModel):
    text: str = Field(min_length=1)
    tone: Literal["natural_student", "academic", "simple_esl"] = "natural_student"
    strength: Literal["light", "balanced", "strong"] = "balanced"
    persona: Literal["esl_student", "freshman", "upper_division", "native_speaker"] = "esl_student"
    coach_feedback: list[dict] | None = None
    preserve_meaning: bool = True
    preserve_citations: bool = False
    preserve_structure: bool = False

    @field_validator("text")
    @classmethod
    def validate_word_limit(cls, value: str) -> str:
        if count_words(value) > settings.max_word_limit:
            raise ValueError(f"Text must be {settings.max_word_limit} words or fewer.")
        return value


class HumanizeResponse(BaseModel):
    rewritten_text: str
    summary_of_changes: str
    key_improvements: list[str] = Field(default_factory=list)
    credits_charged: int
    credits_remaining: int
    input_word_count: int
    rewritten_word_count: int
    billing_redirect: BillingRedirect | None = None


class BillingStatusResponse(BaseModel):
    subscription_status: Literal["free", "starter", "student_plus", "pro"]
    credits_remaining: int
    plan_name: str
    monthly_credit_limit: int
    usage_used: int = 0
    usage_limit: int = 0
    usage_percent: int = 0
    available_credit_packs: list[CheckoutOption]


class CheckoutRequest(BaseModel):
    product_code: Literal[
        "free",
        "starter_monthly",
        "student_plus_monthly",
        "pro_monthly",
        "credit_pack_s",
        "credit_pack_m",
        "credit_pack_l",
    ]
    success_url: str | None = None


class CheckoutResponse(BaseModel):
    checkout_url: str
    message: str


class DemoLoginRequest(BaseModel):
    email: str
    password: str


class DemoLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: str
    user_id: str
    username: str
    nickname: str


class UserResponse(BaseModel):
    email: str
    username: str | None = None
    nickname: str | None = None
    plan_name: str
    credits_remaining: int
    subscription_status: str
    needs_onboarding: bool = False


class DeleteAccountResponse(BaseModel):
    deleted: bool
    message: str


class CompleteOnboardingRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    accepted_terms: bool
    accepted_privacy: bool

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        username = value.strip()
        if not USERNAME_PATTERN.fullmatch(username):
            raise ValueError("Username must use 3-50 letters, numbers, or underscores.")
        return username


class CompleteOnboardingResponse(BaseModel):
    username: str
    onboarded: bool
