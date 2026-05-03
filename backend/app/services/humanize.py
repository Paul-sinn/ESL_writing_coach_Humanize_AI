from __future__ import annotations

import json
from typing import Any

from ..config import get_settings
from ..utils.text import count_words, normalize_whitespace

settings = get_settings()

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]

TONE_INSTRUCTIONS = {
    "natural_student": (
        "Write like a real college student — use contractions, vary sentence length, "
        "add a personal angle where it fits, sound like someone who knows the topic but isn't a robot."
    ),
    "academic": (
        "Maintain a formal academic tone but make it sound like a real person wrote it. "
        "Reduce robotic patterns while keeping appropriate academic vocabulary."
    ),
    "simple_esl": (
        "Use clear, simple English suitable for ESL students. Short sentences, common vocabulary, "
        "direct expression. Easy to read and understand."
    ),
}

STRENGTH_INSTRUCTIONS = {
    "light": "Make minimal changes — fix only the most obvious AI-like phrases and transitions.",
    "balanced": "Make moderate changes — improve naturalness and voice while preserving the student's original ideas.",
    "strong": "Make significant changes — substantially rewrite to maximize natural human voice while keeping all original arguments.",
}


class HumanizeModelService:
    def __init__(self) -> None:
        self._client = OpenAI(api_key=settings.openai_api_key) if (settings.openai_api_key and OpenAI) else None

    def rewrite(
        self,
        text: str,
        tone: str,
        strength: str,
        preserve_meaning: bool,
        preserve_citations: bool,
        preserve_structure: bool,
        model: str,
    ) -> dict[str, Any]:
        if not self._client:
            return self._fallback_rewrite(text)

        preserve_notes = []
        if preserve_meaning:
            preserve_notes.append("Preserve all original arguments and ideas exactly.")
        if preserve_citations:
            preserve_notes.append("Do NOT change any citations, quotes, or references.")
        if preserve_structure:
            preserve_notes.append("Keep the same paragraph structure and organization.")

        tone_instr = TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS["natural_student"])
        strength_instr = STRENGTH_INSTRUCTIONS.get(strength, STRENGTH_INSTRUCTIONS["balanced"])
        preserve_instr = " ".join(preserve_notes) if preserve_notes else ""

        prompt = (
            "You are an expert at rewriting essays to sound more natural, clear, and authentically human.\n\n"
            f"TONE: {tone_instr}\n\n"
            f"REWRITE STRENGTH: {strength_instr}\n\n"
            f"CONSTRAINTS: {preserve_instr}\n\n"
            "AVOID at all costs:\n"
            "- AI buzzwords: 'delve into', 'it is worth noting', 'plays a crucial role', "
            "'in today's world', 'it is essential to', 'shed light on', 'navigate', 'foster', "
            "'furthermore', 'moreover', 'additionally'\n"
            "- Perfectly uniform sentence lengths\n"
            "- Generic transitions — use casual connectors instead\n"
            "- Passive voice overuse\n"
            "- Covering every side equally with no opinion\n\n"
            "Return JSON with keys:\n"
            "- rewritten_text: the full rewritten essay\n"
            "- summary_of_changes: 1-2 sentences describing what changed\n"
            "- key_improvements: list of 3-5 specific improvements made (e.g. 'Replaced AI transitions with natural connectors')"
        )

        response = self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Rewrite this essay:\n\n{text}"},
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or ""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return self._fallback_rewrite(text)

    def _fallback_rewrite(self, text: str) -> dict[str, Any]:
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
            "summary_of_changes": "Adjusted transitions and loosened sentence rhythm to sound less formulaic.",
            "key_improvements": [
                "Replaced AI transition phrases with natural connectors",
                "Reduced overly formal phrasing",
            ],
        }


humanize_service = HumanizeModelService()
