from __future__ import annotations

import re


WORD_RE = re.compile(r"\b[\w'-]+\b")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def count_words(text: str) -> int:
    return len(WORD_RE.findall(text))


def split_sentences(text: str) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []
    parts = [segment.strip() for segment in SENTENCE_RE.split(cleaned) if segment.strip()]
    return parts if parts else [cleaned]


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_minimum_word_count(requirements: str) -> int | None:
    patterns = [
        r"(\d+)\s*\+\s*words",
        r"above\s+(\d+)\s+words",
        r"at\s+least\s+(\d+)\s+words",
        r"minimum\s+(\d+)\s+words",
        r"(\d+)\s+words\s+minimum",
    ]
    lowered = requirements.lower()
    for pattern in patterns:
        match = re.search(pattern, lowered)
        if match:
            return int(match.group(1))
    return None
