from __future__ import annotations

import json
from typing import Any

from ..config import get_settings
from ..utils.text import normalize_whitespace

settings = get_settings()

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]


class AnalysisModelService:
    def __init__(self) -> None:
        self._client = OpenAI(api_key=settings.openai_api_key) if (settings.openai_api_key and OpenAI) else None

    def analyze(self, text: str, sentences: list[str], model_name: str) -> dict[str, Any]:
        if not self._client:
            return self._fallback_analysis(text, sentences)

        prompt = (
            "You are a forensic AI writing detector. Your job is to score text for how likely it was written by an AI (e.g. ChatGPT, Claude, Gemini).\n\n"
            "Score aggressively and accurately. AI-generated text typically shows these patterns:\n"
            "- Uniform sentence length and rhythm with little variation\n"
            "- Overuse of transition words: 'Furthermore', 'Moreover', 'In conclusion', 'Additionally', 'It is important to note'\n"
            "- AI buzzwords: 'delve into', 'it is worth noting', 'plays a crucial role', 'in today's world', 'it is essential to', 'shed light on', 'navigate', 'landscape', 'foster'\n"
            "- Perfect paragraph structure with predictable topic sentence → evidence → conclusion format\n"
            "- Overly formal, polished, and neutral tone with no personal voice\n"
            "- Generic vocabulary, no slang, no contractions, no personality\n"
            "- Repetitive sentence openings (e.g. multiple sentences starting with 'This', 'The', 'It')\n"
            "- Absence of specific personal details, opinions, or emotional variation\n"
            "- Balanced hedging language ('while', 'however', 'on the other hand') used formulaically\n"
            "- Perfect grammar with zero typos — too correct to be human\n"
            "- Every paragraph roughly the same length\n"
            "- Overly comprehensive: covers ALL sides of a topic equally with no strong opinion\n"
            "- Passive voice overuse\n\n"
            "Scoring guide:\n"
            "- 85-100: Almost certainly AI-generated\n"
            "- 60-84: Likely AI-generated or heavily AI-assisted\n"
            "- 40-59: Mixed — possibly AI-assisted with human edits\n"
            "- 0-39: Likely human-written\n\n"
            "When in doubt, score higher. Most AI-generated text will try to look natural — err on the side of flagging it.\n\n"
            "Return ONLY valid JSON with these exact keys:\n"
            "overall_score (int 0-100), summary (1-2 sentence verdict), signals (list of specific patterns found), "
            "sentence_scores (array of {id, text, ai_score, rationale}).\n"
            "Be specific in rationale — cite the actual pattern, not a generic description."
        )
        response = self._client.responses.create(
            model=model_name,
            input=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": f"Analyze this text for AI-likeness:\n\n{text}",
                },
            ],
        )
        content = getattr(response, "output_text", "")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return self._fallback_analysis(text, sentences)

    def _fallback_analysis(self, text: str, sentences: list[str]) -> dict[str, Any]:
        sentence_scores = []
        repeated_markers = ["moreover", "furthermore", "in conclusion", "overall", "therefore"]
        lowered_text = text.lower()
        overall = 38
        signals = []
        if sum(lowered_text.count(marker) for marker in repeated_markers) >= 2:
            overall += 18
            signals.append("Frequent transition phrases create a templated rhythm.")
        if len({len(sentence.split()) for sentence in sentences}) <= max(1, len(sentences) // 3):
            overall += 12
            signals.append("Sentence lengths are unusually uniform.")
        for idx, sentence in enumerate(sentences, start=1):
            score = 32
            rationale_bits = []
            lowered = sentence.lower()
            if any(marker in lowered for marker in repeated_markers):
                score += 25
                rationale_bits.append("uses familiar template transitions")
            if len(sentence.split()) > 26:
                score += 12
                rationale_bits.append("packs many clauses into a polished structure")
            if sentence.count(",") >= 3:
                score += 10
                rationale_bits.append("reads as highly compressed and balanced")
            rationale = normalize_whitespace(", ".join(rationale_bits) or "reads closer to ordinary human variation")
            sentence_scores.append(
                {
                    "text": sentence,
                    "ai_score": min(score, 95),
                    "rationale": rationale,
                    "id": f"sentence-{idx}",
                }
            )
        return {
            "overall_score": min(overall, 95),
            "summary": "The text shows moderate AI-like consistency in rhythm and phrasing.",
            "signals": signals or ["The wording has a fairly normal amount of variation."],
            "sentence_scores": sentence_scores,
        }


analysis_service = AnalysisModelService()
