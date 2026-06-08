from __future__ import annotations

import json
from typing import Any

from ..config import get_settings
from ..utils.text import count_words, detect_output_language, normalize_whitespace


settings = get_settings()

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]

TONE_INSTRUCTIONS = {
    "natural_student": (
        "Write like a real college student. Use contractions freely. Mix short punchy sentences with longer ones. "
        "Add a personal angle where it fits. Sound like someone who knows the topic but isn't trying to impress anyone. "
        "Don't over-polish — real students sometimes repeat a point in a slightly different way."
    ),
    "academic": (
        "Keep a formal academic tone, but make it sound like a real person wrote it. "
        "Use precise vocabulary, but vary your sentence openings and lengths. "
        "Avoid the mechanical precision of AI — a human academic writer occasionally hedges or qualifies."
    ),
    "simple_esl": (
        "Use clear, simple English. Short sentences. Common everyday vocabulary. "
        "Say what you mean without dressing it up. Simple connectors like 'also', 'but', 'so', 'because'. "
        "No complex sentence structures."
    ),
}

STRENGTH_INSTRUCTIONS = {
    "light": "Make minimal changes — fix only the most obvious AI-like phrases and one or two robotic transitions. Leave most sentences intact.",
    "balanced": "Make moderate changes throughout — improve naturalness and voice while keeping the student's original ideas and structure.",
    "strong": "Substantially rewrite for maximum naturalness. Change sentence structure, word choice, and flow aggressively. Break up long uniform sentences. Keep all original arguments but make the writing feel genuinely human.",
}

PERSONA_INSTRUCTIONS = {
    "esl_student": (
        "The writer is a non-native English speaker. Allow slightly imperfect but natural phrasing. "
        "Minor ESL patterns (slightly awkward word order, simpler connectors, occasional missing article) are fine and help authenticity. "
        "Avoid overly polished native-sounding constructions — that's exactly what raises AI flags for ESL writers."
    ),
    "freshman": (
        "The writer is a first-year college student still finding their academic voice. "
        "Sound a bit tentative and earnest — not perfectly confident. "
        "Light hedging ('I think', 'it seems like', 'maybe') is natural. Not every claim needs to sound authoritative."
    ),
    "upper_division": (
        "The writer is an upper-division college student with a confident, established academic voice. "
        "Precise vocabulary and structured argumentation, but still a real person — not a machine. "
        "Occasional direct opinion or personal stance is expected at this level."
    ),
    "native_speaker": (
        "The writer is a native English speaker. Use fully natural American English. "
        "Contractions, informal connectors ('That said,', 'Still,', 'Honestly,', 'Even so,'), varied rhythm. "
        "Short sentences are fine. Don't over-formalize."
    ),
}


def _punctuation_rule(tone: str, persona: str) -> str:
    if tone == "academic" and persona == "upper_division":
        return (
            "Em dashes (—) and semicolons (;) are acceptable but use sparingly — maximum 1-2 per essay total. "
            "Too many still reads as AI-generated."
        )
    return (
        "Do NOT use em dashes (—) or semicolons (;). "
        "These are strong AI detection signals outside of formal academic writing. "
        "Use periods, commas, or plain connectors ('and', 'but', 'so', 'because') instead."
    )


def _language_instruction(text: str) -> str:
    output_language = detect_output_language(text)
    if output_language == "Korean":
        return (
            "OUTPUT LANGUAGE: Korean. Rewrite Korean essays in natural Korean, not English. "
            "All JSON string values, including summary_of_changes and key_improvements, must be in Korean. "
            "Do not translate the essay into English."
        )
    return (
        "OUTPUT LANGUAGE: English. All JSON string values should be in English unless the original essay clearly uses another language."
    )


class HumanizeModelService:
    def __init__(self) -> None:
        self._client = OpenAI(api_key=settings.openai_api_key) if (settings.openai_api_key and OpenAI) else None

    def analyze_for_rewrite(self, text: str, tone: str, strength: str, model: str) -> dict[str, Any]:
        if not self._client:
            return {}
        language_instruction = _language_instruction(text)
        prompt = (
            "You are an expert writing analyst. Analyze the essay and identify:\n\n"
            "1. AI-LIKE PATTERNS: Specific phrases or sentences that sound AI-generated\n"
            "2. REWRITE TARGETS: The 3-5 most important sentences to improve naturalness\n"
            "3. TONE ISSUES: Overall tone problems (e.g. 'too formal', 'uniform sentence length')\n\n"
            f"Target tone: {tone}, Rewrite strength: {strength}\n\n"
            f"{language_instruction}\n\n"
            "Return ONLY valid JSON:\n"
            '{"patterns_found": ["phrase1", ...], '
            '"rewrite_targets": ["sentence1", ...], '
            '"tone_issues": ["issue1", ...]}'
        )
        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text},
                ],
                response_format={"type": "json_object"},
                max_tokens=settings.humanize_analysis_max_tokens,
            )
            return json.loads(response.choices[0].message.content or "{}")
        except Exception:
            return {}

    def rewrite(
        self,
        text: str,
        tone: str,
        strength: str,
        preserve_meaning: bool,
        preserve_citations: bool,
        preserve_structure: bool,
        model: str,
        persona: str = "esl_student",
        analysis: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self._client:
            return self._fallback_rewrite(text)

        original_word_count = count_words(text)
        target_max_words = original_word_count + 100
        preserve_notes = []
        if preserve_meaning:
            preserve_notes.append("Preserve all original arguments and ideas exactly.")
        if preserve_citations:
            preserve_notes.append("Do NOT change any citations, quotes, or references.")
        if preserve_structure:
            preserve_notes.append("Keep the same paragraph structure and organization.")

        tone_instr = TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS["natural_student"])
        strength_instr = STRENGTH_INSTRUCTIONS.get(strength, STRENGTH_INSTRUCTIONS["balanced"])
        persona_instr = PERSONA_INSTRUCTIONS.get(persona, PERSONA_INSTRUCTIONS["esl_student"])
        punct_rule = _punctuation_rule(tone, persona)
        preserve_instr = " ".join(preserve_notes) if preserve_notes else ""
        language_instruction = _language_instruction(text)

        analysis_block = ""
        if analysis:
            analysis_block = (
                "ANALYSIS FINDINGS - use these to guide your rewrite:\n"
                f"- AI patterns found: {analysis.get('patterns_found', [])}\n"
                f"- Priority sentences to rewrite: {analysis.get('rewrite_targets', [])}\n"
                f"- Tone issues: {analysis.get('tone_issues', [])}\n\n"
            )

        prompt = (
            "You are rewriting a student essay to sound more natural and less AI-generated.\n\n"
            f"{language_instruction}\n\n"
            f"WRITER PERSONA: {persona_instr}\n\n"
            f"{analysis_block}"
            f"TONE: {tone_instr}\n\n"
            f"REWRITE STRENGTH: {strength_instr}\n\n"
            f"PUNCTUATION: {punct_rule}\n\n"
            f"CONSTRAINTS: {preserve_instr}\n\n"
            f"LENGTH: The original is {original_word_count} words. "
            f"Stay between {original_word_count} and {target_max_words} words. "
            "Do not shorten significantly -- assignments have word count requirements.\n\n"
            "AVOID (these are strong AI detection signals):\n"
            "- Buzzwords: 'delve into', 'it is worth noting', 'plays a crucial role', "
            "'in today\\'s world', 'it is essential to', 'shed light on', 'navigate', 'foster', "
            "'pivotal', 'underscore', 'tapestry', 'testament to', 'embark', 'robust'\n"
            "- Transition openers: 'Furthermore,', 'Moreover,', 'Additionally,', "
            "'In conclusion,', 'To summarize,', 'In summary,', 'Overall,'\n"
            "- Robotic sentence starters: 'This shows that', 'This demonstrates', "
            "'This highlights', 'This underscores', 'This illustrates', "
            "'One can argue', 'One can see', 'It can be argued'\n"
            "- Meta-essay phrases: 'In this essay', 'This paper will', "
            "'This discussion will', 'As mentioned above', 'As previously stated'\n"
            "- 3+ consecutive sentences starting with the same word ('This', 'The', 'It')\n"
            "- Colon-introduced lists inside body paragraphs\n"
            "- Perfectly uniform sentence lengths (every sentence 18-22 words is a red flag)\n"
            "- Passive voice overuse\n"
            "- Presenting all sides with perfect balance and no personal lean\n\n"
            "NATURAL PATTERNS to use (choose what fits the persona):\n"
            "- Short sentence right after a long one\n"
            "- Light hedging where appropriate: 'I think', 'it seems like', 'probably'\n"
            "- Informal connectors: 'That said,', 'Still,', 'Even so,', 'But', 'So'\n"
            "- Slight rewording of a point instead of one-shot precision\n"
            "- First-person opinion where context allows\n\n"
            "Return JSON with keys:\n"
            "- rewritten_text: the full rewritten essay\n"
            "- summary_of_changes: 1-2 sentences describing what changed\n"
            "- key_improvements: list of 3-5 specific improvements made"
        )

        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Rewrite this essay:\n\n{text}"},
                ],
                response_format={"type": "json_object"},
                max_tokens=settings.humanize_rewrite_max_tokens,
            )
            content = response.choices[0].message.content or ""
            result = json.loads(content)
            return self._repair_if_too_short(
                original_text=text,
                result=result,
                model=model,
                original_word_count=original_word_count,
                target_max_words=target_max_words,
            )
        except Exception:
            return self._fallback_rewrite(text)

    def _repair_if_too_short(
        self,
        original_text: str,
        result: dict[str, Any],
        model: str,
        original_word_count: int,
        target_max_words: int,
    ) -> dict[str, Any]:
        rewritten = result.get("rewritten_text", "")
        rewritten_word_count = count_words(rewritten)
        if rewritten_word_count >= original_word_count * 0.9:
            return result

        repair_prompt = (
            "You are revising an essay rewrite that became too short.\n\n"
            f"{_language_instruction(original_text)}\n\n"
            f"The original essay was {original_word_count} words. "
            f"Expand the current rewrite naturally so it is at least {original_word_count} words "
            f"and no more than about {target_max_words} words.\n"
            "Preserve the original meaning, arguments, citations, paragraph structure, and natural student voice. "
            "Do not add fake facts or unsupported examples.\n\n"
            "Return JSON with keys:\n"
            "- rewritten_text: the expanded rewrite\n"
            "- summary_of_changes: 1-2 sentences describing what changed\n"
            "- key_improvements: list of 3-5 specific improvements made"
        )
        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": repair_prompt},
                    {
                        "role": "user",
                        "content": (
                            f"Original essay:\n{original_text}\n\n"
                            f"Current rewrite ({rewritten_word_count} words):\n{rewritten}"
                        ),
                    },
                ],
                response_format={"type": "json_object"},
                max_tokens=settings.humanize_repair_max_tokens,
            )
            repaired = json.loads(response.choices[0].message.content or "{}")
        except Exception:
            return result

        repaired_text = repaired.get("rewritten_text", "")
        repaired_word_count = count_words(repaired_text)
        original_shortfall = max(0, original_word_count - rewritten_word_count)
        repaired_shortfall = max(0, original_word_count - repaired_word_count)
        if repaired_text and repaired_shortfall < original_shortfall and repaired_word_count <= target_max_words + 100:
            return repaired
        return result

    def _fallback_rewrite(self, text: str) -> dict[str, Any]:
        is_korean = detect_output_language(text) == "Korean"
        sentences = [segment.strip() for segment in text.split(".") if segment.strip()]
        rewritten = ". ".join([
            sentence
            .replace("Furthermore", "On top of that")
            .replace("Moreover", "Another point is")
            .replace("In conclusion", "At the end of the day")
            .replace("Additionally", "Also")
            .replace("It is essential to", "It's important to")
            .replace("It is worth noting", "Worth noting here")
            for sentence in sentences
        ]).strip()
        if rewritten and not rewritten.endswith("."):
            rewritten += "."
        return {
            "rewritten_text": normalize_whitespace(rewritten or text),
            "summary_of_changes": (
                "전환 표현과 문장 리듬을 더 자연스럽게 다듬었습니다."
                if is_korean else
                "Adjusted transitions and loosened sentence rhythm to sound less formulaic."
            ),
            "key_improvements": (
                [
                    "딱딱한 전환 표현을 더 자연스러운 연결로 바꿨습니다.",
                    "지나치게 공식적인 문체를 줄였습니다.",
                ]
                if is_korean else
                [
                    "Replaced AI transition phrases with natural connectors",
                    "Reduced overly formal phrasing",
                ]
            ),
        }


humanize_service = HumanizeModelService()
