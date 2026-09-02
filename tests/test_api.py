"""API tests -- the agent loop is mocked so these never call the real
Anthropic API (no network, no API key required in CI).

Note: ANTHROPIC_API_KEY may already be set in the ambient environment
(e.g. a dev machine also used for other Claude tooling), so every test
that depends on the demo-mode gate sets or clears it explicitly via
monkeypatch rather than relying on what happens to be there.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_redirects_to_docs():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/docs"


@patch("api.app.run_agent", return_value="mocked reply")
def test_chat_returns_a_reply(mock_run_agent, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    response = client.post("/chat", json={"message": "hi", "session_id": "s1"})
    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "mocked reply"
    assert body["session_id"] == "s1"
    mock_run_agent.assert_called_once()


@patch("api.app.run_agent")
def test_chat_runs_in_demo_mode_without_credentials(mock_run_agent, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    response = client.post("/chat", json={"message": "hi", "session_id": "demo"})
    assert response.status_code == 200
    body = response.json()
    assert "demo" in body["reply"].lower()
    assert body["turn_count"] == 0
    mock_run_agent.assert_not_called()


def test_chat_rejects_empty_message():
    response = client.post("/chat", json={"message": ""})
    assert response.status_code == 422
