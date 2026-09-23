import json
from types import SimpleNamespace

import pytest

from backend.categories import NETWORK_VPN
from backend.triage import triage


class _FakeMessage:
    def __init__(self, text):
        self.content = [SimpleNamespace(text=text)]


class _FakeMessages:
    def __init__(self, response_text):
        self._response_text = response_text

    def create(self, **kwargs):
        return _FakeMessage(self._response_text)


class _FakeAnthropicClient:
    def __init__(self, response_text):
        self.messages = _FakeMessages(response_text)


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
