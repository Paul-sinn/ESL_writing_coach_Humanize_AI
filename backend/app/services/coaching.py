from __future__ import annotations

import json
from typing import Any

from ..config import get_settings
from ..utils.text import detect_output_language, split_sentences

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
            return self._fallback_coaching(text, depth)

        assignment_label = ASSIGNMENT_LABELS.get(assignment_type, "Academic writing")
        level_label = LEVEL_LABELS.get(writing_level, "Intermediate")
        output_language = detect_output_language(text)

        if depth == "basic":
            depth_instruction = (
                "Quick Check: identify exactly the top 3 highest-impact issues only. "
                "Keep explanations brief and prioritize what the student should fix first."
            )
        elif depth == "deep":
            depth_instruction = (
                "Deep Feedback: identify 6-8 meaningful issues when the essay is long enough. "
                "For each issue, explain the cause, why it matters for the assignment, and a specific revision direction. "
                "Include paragraph-level issues, voice issues, clarity issues, and sentence-level patterns."
            )
        else:
            depth_instruction = (
                "Full Review: do a comprehensive review with 9-12 issues when the essay is long enough. "
                "Cover sentence-level problems, paragraph flow, evidence/examples, assignment fit, tone, and reader impact. "
                "For every issue include a concrete suggested_revision sentence or phrase the student can compare against the original."
            )

        prompt = (
            "You are an ESL academic writing coach AND writing pattern analyzer.\n\n"
            f"Assignment type: {assignment_label}\n"
            f"Student writing level: {level_label}\n"
            f"Review depth: {depth_instruction}\n\n"
            f"Output language: {output_language}. "
            "All user-facing JSON string values must be in the same language as the student's essay. "
            "Keep quoted original sentences exactly as written in the essay.\n\n"
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
            "give a directional suggestion, explain why_it_matters, and for Full Review include suggested_revision. "
            "Deep Feedback may include suggested_revision for the most important issues. Quick Check should leave suggested_revision null.\n\n"
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
            '     "explanation": "...", "suggestion": "...",\n'
            '     "suggested_revision": "..." or null, "why_it_matters": "..."}\n'
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
            return self._fallback_coaching(text, depth)

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

    def _fallback_coaching(self, text: str, depth: str = "deep") -> dict[str, Any]:
        sentences = split_sentences(text)
        feedback_items = []
        target_count = 3 if depth == "basic" else 7 if depth == "deep" else 10
        output_language = detect_output_language(text)
        is_korean = output_language == "Korean"
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
                            f"'{marker}' 근처 표현은 AI가 자주 쓰는 공식적인 전환어처럼 보여 글이 덜 자연스럽게 느껴질 수 있습니다."
                            if is_korean else
                            f"The phrase near '{marker}' is commonly used in AI-generated text "
                            "and can sound formulaic."
                        ),
                        "suggestion": (
                            "전환어를 더 일상적인 표현으로 바꾸거나, 두 문장의 관계를 직접적으로 연결해 보세요."
                            if is_korean else
                            "Try replacing this transition with something more conversational, "
                            "or connect your ideas more directly."
                        ),
                        "suggested_revision": (
                            sentence.replace("Furthermore", "Also")
                            .replace("Moreover", "Another point is")
                            .replace("In conclusion", "To wrap up")
                        ) if depth == "full_review" else None,
                        "why_it_matters": (
                            "공식적인 전환어가 많으면 실제 초안도 개인적인 글보다 틀에 맞춘 글처럼 보일 수 있습니다."
                            if is_korean else
                            "Formulaic transitions can make a real draft feel less personal and less specific."
                        ),
                    })
                    break

        if sentences and len(feedback_items) < target_count:
            feedback_items.append({
                "sentence": sentences[0].strip(),
                "issue_type": "missing_example",
                "severity": "low",
                "explanation": (
                    "도입부에 구체적인 개인 경험이나 의견이 들어가면 더 설득력 있게 시작할 수 있습니다."
                    if is_korean else
                    "This opening could be stronger with a specific personal example or opinion."
                ),
                "suggestion": (
                    "이 주장과 연결되는 실제 경험이나 구체적인 상황을 한 가지 추가해 보세요."
                    if is_korean else
                    "Think of a real experience you could add here to make the point more vivid."
                ),
                "suggested_revision": None,
                "why_it_matters": (
                    "구체적인 예시는 일반적인 에세이 문체보다 작성자의 목소리를 더 잘 보여 줍니다."
                    if is_korean else
                    "Specific examples help the reader hear your own voice instead of a general essay voice."
                ),
            })
        if depth in ("deep", "full_review") and len(sentences) > 1 and len(feedback_items) < target_count:
            feedback_items.append({
                "sentence": sentences[-1].strip(),
                "issue_type": "clarity_issue",
                "severity": "medium",
                "explanation": (
                    "마무리는 핵심 내용을 반복하는 것보다 독자가 무엇을 이해해야 하는지 더 분명히 보여줄 수 있습니다."
                    if is_korean else
                    "The ending can do more than repeat the main idea."
                ),
                "suggestion": (
                    "주장을 읽고 난 뒤 독자가 가져가야 할 의미를 한 문장으로 덧붙여 보세요."
                    if is_korean else
                    "Add one sentence that explains what the reader should understand after your argument."
                ),
                "suggested_revision": None,
                "why_it_matters": (
                    "좋은 마무리는 단순 문법 수정이 아니라 글 전체의 흐름과 메시지를 강화합니다."
                    if is_korean else
                    "A stronger closing makes the feedback feel connected to the whole essay, not just grammar."
                ),
            })

        if is_korean:
            signals = ["일부 문장이 일반적이거나 공식적인 문체로 느껴질 수 있습니다."]
            strengths = ["핵심 주제가 비교적 분명합니다.", "글의 기본 흐름은 따라가기 쉽습니다."]
            summary = "글의 기본 토대는 좋습니다. 개인적인 목소리와 구체적인 예시를 더하면 더 자연스럽고 설득력 있게 느껴질 수 있습니다."
        else:
            signals = ["Some AI-like transition phrases detected."]
            strengths = [
                "You have a clear main point.",
                "The structure is easy to follow.",
            ]
            summary = (
                "Your essay has a solid foundation. Focus on adding more of your personal voice "
                "and specific examples to make it feel more authentically yours."
            )

        return {
            "ai_like_score": 55,
            "naturalness_score": 45,
            "personal_voice_score": 35,
            "clarity_score": 60,
            "signals": signals,
            "feedback_items": feedback_items[:target_count],
            "strengths": strengths,
            "overall_summary": summary,
        }


coaching_service = CoachingService()
