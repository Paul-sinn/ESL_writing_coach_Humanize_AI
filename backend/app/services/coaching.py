from __future__ import annotations

import json
from typing import Any

from ..config import get_settings

settings = get_settings()

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]

# BLOCKED_PATTERNS = [
#     r"\bbypass\b",
#     r"\bundetectable\b",
#     r"beat\s+turnitin",
#     r"evade\s+detect",
#     r"fool\s+detect",
#     r"pass\s+ai\s+detect",
#     r"no\s+ai\s+score",
#     r"100%\s+human",
#     r"won'?t\s+be\s+(flagged|detected)",
#     r"cheat(ing)?\s+(detector|turnitin|ai)",
#     r"make\s+it\s+undetect",
# ]  # reserved for future chatbot feature

ASSIGNMENT_LABELS: dict[str, str] = {
    "discussion_post": "Discussion Post",
    "reflection_essay": "Reflection Essay",
    "research_essay": "Research Essay",
    "personal_statement": "Personal Statement",
    "general_academic": "Academic Paragraph",
}

LEVEL_LABELS: dict[str, str] = {
    "esl_beginner": "ESL Beginner",
    "intermediate": "Intermediate",
    "advanced": "Advanced",
}


class CoachingService:
    def __init__(self) -> None:
        self._client = OpenAI(api_key=settings.openai_api_key) if (settings.openai_api_key and OpenAI) else None

    # policy_guard reserved for future chatbot feature
    def policy_guard(self, text: str) -> dict[str, Any]:
        return {"blocked": False, "message": ""}

    def analyze_and_coach(
        self,
        text: str,
        assignment_type: str,
        writing_level: str,
        depth: str,
        model: str,
    ) -> dict[str, Any]:
        if not self._client:
            return self._fallback_coaching(text)

        assignment_label = ASSIGNMENT_LABELS.get(assignment_type, "Academic writing")
        level_label = LEVEL_LABELS.get(writing_level, "Intermediate")

        if depth == "basic":
            depth_instruction = "Identify up to 3 key issues. Keep explanations brief."
        elif depth == "deep":
            depth_instruction = "Identify all key issues with clear explanations and actionable suggestions."
        else:
            depth_instruction = (
                "Do a comprehensive review: identify all issues with detailed explanations "
                "and a concrete example rewrite for each suggestion."
            )

        prompt = (
            "You are an ESL academic writing coach AND writing pattern analyzer.\n\n"
            f"Assignment type: {assignment_label}\n"
            f"Student writing level: {level_label}\n"
            f"Review depth: {depth_instruction}\n\n"
            "Analyze the student's text and return:\n\n"
            "1. FOUR WRITING SCORES (0-100):\n"
            "   - ai_like_score: How much the writing resembles AI-generated text (higher = more AI-like)\n"
            "   - naturalness_score: How natural and human the writing feels (higher = more natural)\n"
            "   - personal_voice_score: How much the student's own voice and examples come through\n"
            "   - clarity_score: How clear and well-structured the writing is\n\n"
            "2. SIGNALS: List 2-4 specific writing patterns detected (e.g. 'Uniform sentence length', "
            "'AI transition phrases detected')\n\n"
            "3. FEEDBACK ITEMS for specific problematic sentences:\n"
            "   Issue types: ai_pattern | unnatural_english | robotic_tone | missing_example | clarity_issue\n"
            "   Severity: 'high' (very obvious issue), 'medium' (moderate), 'low' (minor)\n"
            "   For each item: quote the sentence, explain WHY it sounds generic/unnatural (simple encouraging language), "
            "give a directional suggestion — NOT a full rewrite.\n\n"
            "4. STRENGTHS: 2-3 genuine positive aspects\n\n"
            "5. OVERALL SUMMARY: 1-2 sentences\n\n"
            "Tone: Encouraging, educational, supportive coach — not a detector.\n\n"
            "Return ONLY valid JSON:\n"
            "{\n"
            '  "ai_like_score": 0-100,\n'
            '  "naturalness_score": 0-100,\n'
            '  "personal_voice_score": 0-100,\n'
            '  "clarity_score": 0-100,\n'
            '  "signals": ["..."],\n'
            '  "feedback_items": [\n'
            '    {"sentence": "...", "issue_type": "...", "severity": "high|medium|low",\n'
            '     "explanation": "...", "suggestion": "..."}\n'
            "  ],\n"
            '  "strengths": ["..."],\n'
            '  "overall_summary": "..."\n'
            "}"
        )

        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Please analyze and coach my writing:\n\n{text}"},
                ],
                response_format={"type": "json_object"},
                max_tokens=settings.coach_max_tokens,
            )
            content = response.choices[0].message.content or ""
            return json.loads(content)
        except Exception:
            return self._fallback_coaching(text)

    def generate_integrity_content(self) -> dict[str, Any]:
        return {
            "integrity_note": (
                "Remember to follow your school's AI use policy. This tool helps you improve "
                "your own writing — the ideas, arguments, and final version should be yours."
            ),
            "disclosure_statement": (
                "Optional disclosure you can add to your submission: "
                '"I used an AI writing coach to review grammar and improve clarity. '
                'The ideas, arguments, and final revisions are my own."'
            ),
        }

    def _fallback_coaching(self, text: str) -> dict[str, Any]:
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        feedback_items = []
        ai_markers = [
            "furthermore", "moreover", "in conclusion", "it is essential",
            "plays a crucial role", "delve into", "shed light on", "it is worth noting",
        ]
        for sentence in sentences[:6]:
            lowered = sentence.lower()
            for marker in ai_markers:
                if marker in lowered:
                    feedback_items.append({
                        "sentence": sentence.strip(),
                        "issue_type": "ai_pattern",
                        "severity": "medium",
                        "explanation": (
                            f"The phrase near '{marker}' is commonly used in AI-generated text "
                            "and can sound formulaic."
                        ),
                        "suggestion": (
                            "Try replacing this transition with something more conversational, "
                            "or connect your ideas more directly."
                        ),
                    })
                    break

        if not feedback_items and sentences:
            feedback_items.append({
                "sentence": sentences[0].strip(),
                "issue_type": "missing_example",
                "severity": "low",
                "explanation": "This opening could be stronger with a specific personal example or opinion.",
                "suggestion": "Think of a real experience you could add here to make the point more vivid.",
            })

        return {
            "ai_like_score": 55,
            "naturalness_score": 45,
            "personal_voice_score": 35,
            "clarity_score": 60,
            "signals": ["Some AI-like transition phrases detected."],
            "feedback_items": feedback_items[:5],
            "strengths": [
                "You have a clear main point.",
                "The structure is easy to follow.",
            ],
            "overall_summary": (
                "Your essay has a solid foundation. Focus on adding more of your personal voice "
                "and specific examples to make it feel more authentically yours."
            ),
        }


coaching_service = CoachingService()
