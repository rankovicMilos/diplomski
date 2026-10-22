import base64
from types import SimpleNamespace

import pytest

from src.services import llm_service


class FakeStream:
    def __init__(self, message):
        self.message = message

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get_final_message(self):
        return self.message


@pytest.fixture
def fake_client(monkeypatch):
    calls = []

    def install(message):
        def stream(**kwargs):
            calls.append(kwargs)
            return FakeStream(message)

        client = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(stream=stream)))
        monkeypatch.setattr(llm_service, "_client", lambda: client)
        return calls

    return install


def message(stop_reason="end_turn", blocks=None):
    return SimpleNamespace(
        model="claude-sonnet-5-5",
        stop_reason=stop_reason,
        usage=SimpleNamespace(input_tokens=10, output_tokens=5),
        content=blocks if blocks is not None else [
            SimpleNamespace(type="thinking", thinking=""),
            SimpleNamespace(type="text", text='{"a": '),
            SimpleNamespace(type="text", text="1}"),
        ],
    )


def test_joins_text_blocks_only(fake_client):
    calls = fake_client(message())

    result = llm_service.generate_only("context", "system")

    assert result == {"output": {"text": '{"a": 1}'}}
    request = calls[0]
    assert request["system"] == "system"
    assert request["messages"] == [{"role": "user", "content": [{"type": "text", "text": "context"}]}]
    assert request["fallbacks"] == "default"
    assert "temperature" not in request


def test_pdf_is_sent_as_document_before_text(fake_client):
    calls = fake_client(message())

    llm_service.generate_with_pdf(b"%PDF-1.4", "params", "system")

    document, text = calls[0]["messages"][0]["content"]
    assert document["type"] == "document"
    assert document["source"]["media_type"] == "application/pdf"
    assert base64.b64decode(document["source"]["data"]) == b"%PDF-1.4"
    assert text == {"type": "text", "text": "params"}


def test_section_context_lists_sources_per_section(fake_client):
    calls = fake_client(message())

    result = llm_service.generate_with_section_context(
        {"market_overview": [{"location": "raw/a.md", "content": "Proizvodnja 2025"}], "empty": []},
        "system", "Generate", section_labels={"market_overview": "MARKET OVERVIEW DATA"},
    )

    user_text = calls[0]["messages"][0]["content"][0]["text"]
    assert "=== MARKET OVERVIEW DATA ===" in user_text
    assert "[MARKET_OVERVIEW Source 1: raw/a.md]\nProizvodnja 2025" in user_text
    assert "EMPTY" not in user_text
    assert result["citations"] == []


def test_refusal_raises(fake_client):
    fake_client(message(stop_reason="refusal", blocks=[]))

    with pytest.raises(llm_service.GenerationRefused):
        llm_service.generate_only("context", "system")


def test_truncated_output_is_returned(fake_client):
    fake_client(message(stop_reason="max_tokens", blocks=[SimpleNamespace(type="text", text='{"a"')]))

    assert llm_service.generate_only("c", "s") == {"output": {"text": '{"a"'}}
