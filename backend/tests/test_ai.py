from unittest.mock import patch

import pytest

from backend.app import ai


def test_get_api_key_missing(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY is not set"):
        ai.get_api_key()


def test_get_api_key_present(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-123")
    assert ai.get_api_key() == "test-key-123"


def test_chat_success(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-key")

    mock_response = {
        "choices": [{"message": {"content": "4"}}]
    }

    with patch("backend.app.ai.httpx.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status = lambda: None

        result = ai.chat([{"role": "user", "content": "What is 2+2?"}])

    assert result == "4"
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args
    assert call_kwargs.kwargs["json"]["model"] == "openai/gpt-oss-120b"
    assert "Bearer fake-key" in call_kwargs.kwargs["headers"]["Authorization"]


def test_ai_test_endpoint(client, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-key")

    mock_response = {
        "choices": [{"message": {"content": "4"}}]
    }

    with patch("backend.app.ai.httpx.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status = lambda: None

        r = client.get("/api/ai/test")

    assert r.status_code == 200
    assert r.json()["reply"] == "4"
