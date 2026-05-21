"""Tests for structured AI chat: schema validation, action application, and endpoint."""

import json
from unittest.mock import patch

from backend.app.ai_chat import parse_ai_response, apply_actions, load_board_json


# --- parse_ai_response tests ---


def test_parse_simple_reply():
    raw = json.dumps({"reply": "Hello!", "actions": []})
    resp = parse_ai_response(raw)
    assert resp.reply == "Hello!"
    assert resp.actions == []


def test_parse_with_actions():
    raw = json.dumps({
        "reply": "Done!",
        "actions": [
            {"action": "create", "column_id": 1, "title": "New task", "details": ""},
            {"action": "delete", "card_id": 5},
        ],
    })
    resp = parse_ai_response(raw)
    assert resp.reply == "Done!"
    assert len(resp.actions) == 2
    assert resp.actions[0]["action"] == "create"
    assert resp.actions[1]["action"] == "delete"


def test_parse_strips_markdown_fences():
    raw = "```json\n" + json.dumps({"reply": "Hi", "actions": []}) + "\n```"
    resp = parse_ai_response(raw)
    assert resp.reply == "Hi"


def test_parse_no_actions_field():
    raw = json.dumps({"reply": "Just chatting"})
    resp = parse_ai_response(raw)
    assert resp.reply == "Just chatting"
    assert resp.actions == []


def test_parse_invalid_json():
    import pytest
    with pytest.raises((json.JSONDecodeError, Exception)):
        parse_ai_response("not json at all")


# --- apply_actions tests ---


def test_apply_create_action(tmp_db):
    board = load_board_json(1)
    col_id = board["columns"][0]["id"]

    results = apply_actions([
        {"action": "create", "column_id": col_id, "title": "AI card", "details": "Created by AI"}
    ])

    assert len(results) == 1
    assert "Created card" in results[0]

    # Verify in DB
    board_after = load_board_json(1)
    cards = board_after["columns"][0]["cards"]
    assert any(c["title"] == "AI card" for c in cards)


def test_apply_update_action(tmp_db):
    # Create a card first
    from backend.app.database import get_connection
    conn = get_connection()
    conn.execute("INSERT INTO cards (column_id, title, details, position) VALUES (1, 'Old', '', 0)")
    conn.commit()
    card_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()

    results = apply_actions([
        {"action": "update", "card_id": card_id, "title": "New title", "details": "New details"}
    ])

    assert "Updated card" in results[0]

    board = load_board_json(1)
    cards = board["columns"][0]["cards"]
    card = next(c for c in cards if c["id"] == card_id)
    assert card["title"] == "New title"
    assert card["details"] == "New details"


def test_apply_move_action(tmp_db):
    from backend.app.database import get_connection
    conn = get_connection()
    conn.execute("INSERT INTO cards (column_id, title, details, position) VALUES (1, 'Mover', '', 0)")
    conn.commit()
    card_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()

    results = apply_actions([
        {"action": "move", "card_id": card_id, "column_id": 2, "position": 0}
    ])

    assert "Moved card" in results[0]

    board = load_board_json(1)
    col2_cards = board["columns"][1]["cards"]
    assert any(c["id"] == card_id for c in col2_cards)


def test_apply_delete_action(tmp_db):
    from backend.app.database import get_connection
    conn = get_connection()
    conn.execute("INSERT INTO cards (column_id, title, details, position) VALUES (1, 'Doomed', '', 0)")
    conn.commit()
    card_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()

    results = apply_actions([
        {"action": "delete", "card_id": card_id}
    ])

    assert "Deleted card" in results[0]

    board = load_board_json(1)
    cards = board["columns"][0]["cards"]
    assert not any(c["id"] == card_id for c in cards)


def test_apply_unknown_action(tmp_db):
    results = apply_actions([{"action": "fly", "card_id": 1}])
    assert "Unknown action" in results[0]


def test_apply_card_not_found(tmp_db):
    results = apply_actions([{"action": "delete", "card_id": 9999}])
    assert "not found" in results[0]


# --- Endpoint test ---


def test_ai_chat_endpoint(client, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-key")

    ai_reply = json.dumps({
        "reply": "I created a card for you.",
        "actions": [{"action": "create", "column_id": 1, "title": "From AI", "details": ""}],
    })

    mock_response = {"choices": [{"message": {"content": ai_reply}}]}

    with patch("backend.app.ai.httpx.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status = lambda: None

        r = client.post("/api/ai/chat", json={
            "user_id": 1,
            "messages": [{"role": "user", "content": "Create a task called From AI"}],
        })

    assert r.status_code == 200
    data = r.json()
    assert data["reply"] == "I created a card for you."
    assert len(data["actions_applied"]) == 1
    assert "Created card" in data["actions_applied"][0]

    # Verify card was actually created
    board = client.get("/api/board/1").json()
    all_cards = [c for col in board["columns"] for c in col["cards"]]
    assert any(c["title"] == "From AI" for c in all_cards)


def test_ai_chat_no_actions(client, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-key")

    ai_reply = json.dumps({"reply": "Just chatting!", "actions": []})
    mock_response = {"choices": [{"message": {"content": ai_reply}}]}

    with patch("backend.app.ai.httpx.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status = lambda: None

        r = client.post("/api/ai/chat", json={
            "user_id": 1,
            "messages": [{"role": "user", "content": "Hello"}],
        })

    assert r.status_code == 200
    assert r.json()["reply"] == "Just chatting!"
    assert r.json()["actions_applied"] == []
