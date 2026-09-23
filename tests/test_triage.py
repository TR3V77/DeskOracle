import os

import pytest

from backend.triage import triage, _fallback_classify


@pytest.fixture(autouse=True)
def force_fallback_mode(monkeypatch):
    """Ensure tests run deterministically against the rule-based fallback,
    regardless of whether an ANTHROPIC_API_KEY is set in the environment."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


@pytest.mark.parametrize(
    "description,expected_category",
    [
        ("My VPN won't connect and keeps failing authentication", "Network_VPN"),
        ("I forgot my password and I'm locked out of my account", "Account_Access"),
        ("The printer on the 2nd floor is offline", "Printer"),
        ("I think I clicked a phishing link in an email", "Security"),
        ("My laptop battery won't charge anymore", "Hardware"),
        ("Outlook is stuck in offline mode and I can't send email", "Email"),
        ("Need Photoshop installed, license activation error", "Software"),
    ],
)
def test_fallback_classify_category(description, expected_category):
    category, _ = _fallback_classify(description)
    assert category == expected_category


def test_fallback_flags_security_as_high_or_critical():
    _, priority = _fallback_classify("I think I clicked a phishing link and entered my password")
    assert priority in ("High", "Critical")


def test_triage_end_to_end_returns_fallback_mode():
    response = triage("VPN keeps disconnecting every few minutes")
    assert response.mode == "rule_based_fallback"
    assert response.predicted_category == "Network_VPN"
    assert len(response.kb_matches) > 0
    assert response.suggested_response
