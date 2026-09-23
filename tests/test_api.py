import os

import pytest
from fastapi.testclient import TestClient

os.environ.pop("ANTHROPIC_API_KEY", None)

from backend.app import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_triage_endpoint_returns_expected_shape():
    response = client.post(
        "/tickets/triage", json={"description": "My VPN keeps disconnecting"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "predicted_category" in data
    assert "predicted_priority" in data
    assert "suggested_response" in data
    assert "kb_matches" in data


def test_triage_endpoint_rejects_too_short_description():
    response = client.post("/tickets/triage", json={"description": "hi"})
    assert response.status_code == 422
