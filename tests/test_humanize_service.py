import json

from backend.app.services.humanize import HumanizeModelService


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

    def create(self, **kwargs):
        self.calls += 1
        return _Response(self.payloads[self.calls - 1])


class _FakeChat:
    def __init__(self, completions: _FakeCompletions) -> None:
        self.completions = completions


class _FakeClient:
    def __init__(self, payloads: list[dict]) -> None:
        self.completions = _FakeCompletions(payloads)
        self.chat = _FakeChat(self.completions)


def _service_with_payloads(payloads: list[dict]) -> tuple[HumanizeModelService, _FakeClient]:
    service = HumanizeModelService()
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
