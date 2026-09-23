"""
Triage engine: given a raw ticket description, retrieves relevant KB
articles (backend.rag) and produces a predicted category, priority, and a
suggested response.

Two modes:
  - "llm": calls Claude (via the anthropic SDK) with the retrieved KB
    context, used when ANTHROPIC_API_KEY is set. This is the "AI agent"
    path -- it reasons over the retrieved context rather than pattern
    matching.
  - "rule_based_fallback": deterministic keyword classifier used when no
    API key is configured (or the call fails), so the app is always
    demoable and testable offline, and so the analytics evaluation can run
    for free and deterministically against a known ground truth.
"""
import json
import logging
import os
import re

from backend.categories import (
    ACCOUNT_ACCESS,
    CATEGORIES,
    EMAIL,
    HARDWARE,
    NETWORK_VPN,
    OTHER,
    PRINTER,
    SECURITY,
    SOFTWARE,
)
from backend.models import KBMatch, TriageResponse
from backend.rag import KnowledgeBase

logger = logging.getLogger(__name__)

_kb = KnowledgeBase()

# Keyword sets used by the offline fallback classifier. Order matters:
# first matching category wins, so more specific/urgent categories are
# checked before general ones.
_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    SECURITY: ["phishing", "suspicious email", "malware", "virus", "hacked",
               "clicked a link", "ransomware", "compromised"],
    NETWORK_VPN: ["vpn", "wifi", "wi-fi", "network", "connect to the internet",
                  "disconnect"],
    ACCOUNT_ACCESS: ["password", "locked out", "access", "login", "log in",
                      "account", "permission", "provision"],
    PRINTER: ["printer", "print job", "printing", "spooler"],
    EMAIL: ["email", "mailbox", "outlook", "inbox", "bounce"],
    HARDWARE: ["laptop", "battery", "screen", "monitor", "dock", "keyboard",
               "won't power on", "overheating", "fan"],
    SOFTWARE: ["install", "license", "application", "software", "crash",
               "freeze", "update"],
}

_URGENT_KEYWORDS = ["urgent", "asap", "can't work", "cannot work", "critical",
                     "down", "breach", "compromised", "entire team", "production"]
_HIGH_KEYWORDS = ["not working", "won't", "can't", "error", "failed", "blocked"]


def _fallback_classify(description: str) -> tuple[str, str]:
    text = description.lower()

    category = OTHER
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            category = cat
            break

    if category == SECURITY:
        priority = "Critical" if any(kw in text for kw in _URGENT_KEYWORDS) else "High"
    elif any(kw in text for kw in _URGENT_KEYWORDS):
        priority = "Critical"
    elif any(kw in text for kw in _HIGH_KEYWORDS):
        priority = "High"
    else:
        priority = "Medium"

    return category, priority


def _fallback_response(category: str, kb_matches) -> str:
    if not kb_matches:
        return (
            "Thanks for the report -- this doesn't clearly match an existing "
            "knowledge base article, so it's been routed to a general IT agent "
            "for manual triage."
        )
    top = kb_matches[0][0]
    return (
        f"This looks like a {category.replace('_', '/')} issue. Based on "
        f"'{top.title}', try the standard steps in that article first. "
        f"If that doesn't resolve it, this ticket will be escalated to a "
        f"specialist for the {category.replace('_', '/')} queue."
    )


def _llm_classify(description: str, kb_matches) -> dict | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic
    except ImportError:
        return None

    context = "\n\n".join(
        f"[{article.category}] {article.title}\n{article.body}" for article, _ in kb_matches
    )
    category_options = ", ".join([*CATEGORIES, OTHER])
    prompt = f"""You are an IT helpdesk triage agent. A new ticket has come in.

Ticket description: "{description}"

Relevant internal knowledge base articles:
{context if context else "(no close match found)"}

Respond with ONLY a JSON object with these exact keys:
- "category": one of {category_options}
- "priority": one of Low, Medium, High, Critical
- "suggested_response": a 2-3 sentence draft reply to the employee, citing the
  relevant KB steps if applicable.
"""
    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        # claude-sonnet-5 runs adaptive thinking by default, so content[0] may
        # be a thinking block rather than text -- scan for the text block
        # instead of assuming position.
        text = next((block.text for block in message.content if block.type == "text"), None)
        if text is None:
            logger.warning("LLM response contained no text block; falling back to rule-based classifier")
            return None
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            logger.warning("LLM response contained no JSON object; falling back to rule-based classifier")
            return None
        return json.loads(match.group(0))
    except Exception:
        logger.exception("LLM classification failed; falling back to rule-based classifier")
        return None


def triage(description: str) -> TriageResponse:
    kb_matches = _kb.search(description, top_k=3)
    kb_match_models = [
        KBMatch(title=a.title, category=a.category, score=round(float(s), 3), body=a.body)
        for a, s in kb_matches
    ]

    llm_result = _llm_classify(description, kb_matches)
    if llm_result is not None:
        return TriageResponse(
            predicted_category=llm_result.get("category", "Other"),
            predicted_priority=llm_result.get("priority", "Medium"),
            suggested_response=llm_result.get("suggested_response", ""),
            kb_matches=kb_match_models,
            mode="llm",
        )

    category, priority = _fallback_classify(description)
    suggested_response = _fallback_response(category, kb_matches)
    return TriageResponse(
        predicted_category=category,
        predicted_priority=priority,
        suggested_response=suggested_response,
        kb_matches=kb_match_models,
        mode="rule_based_fallback",
    )
