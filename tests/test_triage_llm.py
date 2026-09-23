import json
from types import SimpleNamespace

import pytest

from backend.categories import NETWORK_VPN
from backend.triage import triage


class _FakeMessage:
    def __init__(self, text, include_thinking_block=False):
        content = []
        if include_thinking_block:
            content.append(SimpleNamespace(type="thinking", thinking="reasoning about the ticket..."))
        content.append(SimpleNamespace(type="text", text=text))
        self.content = content


class _FakeMessages:
    def __init__(self, response_text, include_thinking_block=False):
        self._response_text = response_text
        self._include_thinking_block = include_thinking_block

    def create(self, **kwargs):
        return _FakeMessage(self._response_text, self._include_thinking_block)


class _FakeAnthropicClient:
    def __init__(self, response_text, include_thinking_block=False):
        self.messages = _FakeMessages(response_text, include_thinking_block)


@pytest.fixture
def api_key_set(monkeypatch):
    """LLM mode only activates when ANTHROPIC_API_KEY is set."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


def test_llm_path_parses_well_formed_response(monkeypatch, api_key_set):
    response_json = json.dumps({
        "category": NETWORK_VPN,
        "priority": "High",
        "suggested_response": "Please restart your VPN client and reconnect.",
    })
    monkeypatch.setattr("anthropic.Anthropic", lambda **kwargs: _FakeAnthropicClient(response_json))

    result = triage("My VPN keeps disconnecting")

    assert result.mode == "llm"
    assert result.predicted_category == NETWORK_VPN
    assert result.predicted_priority == "High"
    assert result.suggested_response == "Please restart your VPN client and reconnect."


def test_llm_path_falls_back_on_malformed_response(monkeypatch, api_key_set):
    monkeypatch.setattr(
        "anthropic.Anthropic",
        lambda **kwargs: _FakeAnthropicClient("not valid json, no braces here"),
    )

    result = triage("My VPN keeps disconnecting")

    assert result.mode == "rule_based_fallback"
    assert result.predicted_category == NETWORK_VPN


def test_llm_path_falls_back_on_client_exception(monkeypatch, api_key_set):
    def _raise(**kwargs):
        raise RuntimeError("simulated API failure")

    monkeypatch.setattr("anthropic.Anthropic", _raise)

    result = triage("My VPN keeps disconnecting")

    assert result.mode == "rule_based_fallback"


def test_llm_path_finds_text_block_after_leading_thinking_block(monkeypatch, api_key_set):
    """claude-sonnet-5 runs adaptive thinking by default, so a thinking block
    can precede the text block in response.content -- the parser must not
    assume content[0] is text."""
    response_json = json.dumps({
        "category": NETWORK_VPN,
        "priority": "High",
        "suggested_response": "Please restart your VPN client and reconnect.",
    })
    monkeypatch.setattr(
        "anthropic.Anthropic",
        lambda **kwargs: _FakeAnthropicClient(response_json, include_thinking_block=True),
    )

    result = triage("My VPN keeps disconnecting")

    assert result.mode == "llm"
    assert result.predicted_category == NETWORK_VPN


def test_llm_path_falls_back_when_no_text_block_present(monkeypatch, api_key_set):
    """If the response is cut off (e.g. max_tokens hit mid-thinking), there
    may be no text block at all -- must fall back cleanly, not raise."""
    class _ThinkingOnlyMessage:
        content = [SimpleNamespace(type="thinking", thinking="still reasoning...")]

    class _ThinkingOnlyMessages:
        def create(self, **kwargs):
            return _ThinkingOnlyMessage()

    class _ThinkingOnlyClient:
        def __init__(self, **kwargs):
            self.messages = _ThinkingOnlyMessages()

    monkeypatch.setattr("anthropic.Anthropic", _ThinkingOnlyClient)

    result = triage("My VPN keeps disconnecting")

    assert result.mode == "rule_based_fallback"
    assert result.predicted_category == NETWORK_VPN
