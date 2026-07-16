import json

from backend.app.services.rewriter import RewriterModelService


class _Message:
    def __init__(self, content: str) -> None:
        self.content = content


class _Choice:
    def __init__(self, content: str) -> None:
        self.message = _Message(content)


class _Response:
    def __init__(self, payload: dict) -> None:
        self.choices = [_Choice(json.dumps(payload))]


class _FakeCompletions:
    def __init__(self, payloads: list[dict]) -> None:
        self.payloads = payloads
        self.calls = 0
        self.kwargs: list[dict] = []

    def create(self, **kwargs):
        self.calls += 1
        self.kwargs.append(kwargs)
        return _Response(self.payloads[self.calls - 1])


class _FakeChat:
    def __init__(self, completions: _FakeCompletions) -> None:
        self.completions = completions


class _FakeClient:
    def __init__(self, payloads: list[dict]) -> None:
        self.completions = _FakeCompletions(payloads)
        self.chat = _FakeChat(self.completions)


def _service_with_payloads(payloads: list[dict]) -> tuple[RewriterModelService, _FakeClient]:
    service = RewriterModelService()
    client = _FakeClient(payloads)
    service._client = client
    return service, client


def test_rewrite_does_not_repair_when_output_is_at_least_90_percent_length():
    original = " ".join(f"word{i}" for i in range(20))
    service, client = _service_with_payloads([
        {
            "rewritten_text": " ".join(f"rewrite{i}" for i in range(18)),
            "summary_of_changes": "Kept the essay close to the original length.",
            "key_improvements": [],
        }
    ])

    result = service.rewrite(
        original,
        tone="natural_student",
        strength="balanced",
        preserve_meaning=True,
        preserve_citations=False,
        preserve_structure=False,
        model="gpt-4o",
    )

    assert client.completions.calls == 1
    assert len(result["rewritten_text"].split()) == 18


def test_rewrite_repairs_once_when_output_is_more_than_10_percent_shorter():
    original = " ".join(f"word{i}" for i in range(20))
    service, client = _service_with_payloads([
        {
            "rewritten_text": "too short rewrite",
            "summary_of_changes": "Shortened too much.",
            "key_improvements": [],
        },
        {
            "rewritten_text": " ".join(f"expanded{i}" for i in range(20)),
            "summary_of_changes": "Expanded the rewrite to preserve assignment length.",
            "key_improvements": ["Restored length"],
        },
    ])

    result = service.rewrite(
        original,
        tone="natural_student",
        strength="balanced",
        preserve_meaning=True,
        preserve_citations=False,
        preserve_structure=False,
        model="gpt-4o",
    )

    assert client.completions.calls == 2
    assert len(result["rewritten_text"].split()) == 20
    assert result["summary_of_changes"] == "Expanded the rewrite to preserve assignment length."


def test_rewrite_returns_original_short_result_when_repair_does_not_improve_length():
    original = " ".join(f"word{i}" for i in range(20))
    service, client = _service_with_payloads([
        {
            "rewritten_text": "too short rewrite",
            "summary_of_changes": "Shortened too much.",
            "key_improvements": [],
        },
        {
            "rewritten_text": "still short",
            "summary_of_changes": "Still short.",
            "key_improvements": [],
        },
    ])

    result = service.rewrite(
        original,
        tone="natural_student",
        strength="balanced",
        preserve_meaning=True,
        preserve_citations=False,
        preserve_structure=False,
        model="gpt-4o",
    )

    assert client.completions.calls == 2
    assert result["rewritten_text"] == "too short rewrite"


def test_rewrite_korean_input_instructs_korean_output():
    original = "저는 수업에서 배운 내용을 바탕으로 이 글을 썼습니다. 제 경험도 함께 설명하고 싶습니다."
    service, client = _service_with_payloads([
        {
            "rewritten_text": "저는 수업에서 배운 내용을 바탕으로 이 글을 썼습니다. 제 경험도 함께 더 자연스럽게 설명하고 싶습니다.",
            "summary_of_changes": "문장을 더 자연스럽게 다듬었습니다.",
            "key_improvements": ["한국어 문체를 유지했습니다."],
        }
    ])

    service.rewrite(
        original,
        tone="natural_student",
        strength="balanced",
        preserve_meaning=True,
        preserve_citations=False,
        preserve_structure=False,
        model="gpt-4o",
    )

    system_prompt = client.completions.kwargs[0]["messages"][0]["content"]
    assert "rewritten_text must stay in natural Korean" in system_prompt
    assert "Do not translate the essay into English" in system_prompt
    assert "summary_of_changes" in system_prompt
    assert "must be in English" in system_prompt


def test_analyze_for_rewrite_does_not_limit_targets_to_three_to_five_sentences():
    service, client = _service_with_payloads([
        {
            "patterns_found": [],
            "rewrite_targets": [],
            "tone_issues": [],
            "voice_opportunities": [],
        }
    ])

    service.analyze_for_rewrite(
        "This essay sounds generic. It needs more natural rhythm.",
        tone="natural_student",
        strength="balanced",
        model="gpt-4o",
    )

    system_prompt = client.completions.kwargs[0]["messages"][0]["content"]
    assert "Do not limit this to 3-5 sentences" in system_prompt
    assert "VOICE OPPORTUNITIES" in system_prompt
    assert '"voice_opportunities"' in system_prompt


def test_rewrite_prompt_requires_full_draft_rewrite_and_blocks_em_dashes_by_default():
    original = "This essay explains my experience in class and why it mattered to me."
    service, client = _service_with_payloads([
        {
            "rewritten_text": original,
            "summary_of_changes": "Kept the draft natural.",
            "key_improvements": [],
        }
    ])

    service.rewrite(
        original,
        tone="natural_student",
        strength="balanced",
        preserve_meaning=True,
        preserve_citations=False,
        preserve_structure=False,
        model="gpt-4o",
        persona="esl_student",
        analysis={"voice_opportunities": ["Use a more direct student stance."]},
    )

    system_prompt = client.completions.kwargs[0]["messages"][0]["content"]
    assert "Rewrite the essay as a complete draft" in system_prompt
    assert "Paraphrase broadly" in system_prompt
    assert "Do NOT use em dashes or semicolons" in system_prompt
    assert "Voice opportunities" in system_prompt
    assert "—" not in system_prompt


def test_rewrite_prompt_allows_very_limited_em_dashes_for_native_persona():
    original = "The class helped me understand the topic in a more practical way."
    service, client = _service_with_payloads([
        {
            "rewritten_text": original,
            "summary_of_changes": "Kept the draft natural.",
            "key_improvements": [],
        }
    ])

    service.rewrite(
        original,
        tone="natural_student",
        strength="balanced",
        preserve_meaning=True,
        preserve_citations=False,
        preserve_structure=False,
        model="gpt-4o",
        persona="native_speaker",
    )

    system_prompt = client.completions.kwargs[0]["messages"][0]["content"]
    assert "hard maximum of 1-2 total per essay" in system_prompt
    assert "Do not use them by default" in system_prompt


def test_fallback_rewrite_korean_input_keeps_metadata_in_english():
    service = RewriterModelService()
    service._client = None

    result = service.rewrite(
        "저는 제 경험을 통해 이 주제를 이해하게 되었습니다.",
        tone="natural_student",
        strength="balanced",
        preserve_meaning=True,
        preserve_citations=False,
        preserve_structure=False,
        model="gpt-4o",
    )

    assert "Korean" in result["summary_of_changes"]
    assert result["key_improvements"][0] == "Preserved the original essay language"
