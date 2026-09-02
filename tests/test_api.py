"""API tests -- the agent loop is mocked so these never call the real
Anthropic API (no network, no API key required in CI)."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("api.app.run_agent", return_value="mocked reply")
def test_chat_returns_a_reply(mock_run_agent):
    response = client.post("/chat", json={"message": "hi", "session_id": "s1"})
    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "mocked reply"
    assert body["session_id"] == "s1"
    mock_run_agent.assert_called_once()


def test_chat_rejects_empty_message():
    response = client.post("/chat", json={"message": ""})
    assert response.status_code == 422
