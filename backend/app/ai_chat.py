"""Structured AI chat: sends board state + history to the model, parses response with optional board updates."""

import json

from pydantic import BaseModel

from backend.app.ai import chat
from backend.app.database import get_connection


# --- Response schema ---


class CardCreateAction(BaseModel):
    action: str = "create"
    column_id: int
    title: str
    details: str = ""


class CardUpdateAction(BaseModel):
    action: str = "update"
    card_id: int
    title: str | None = None
    details: str | None = None


class CardMoveAction(BaseModel):
    action: str = "move"
    card_id: int
    column_id: int
    position: int


class CardDeleteAction(BaseModel):
    action: str = "delete"
    card_id: int


class AIResponse(BaseModel):
    reply: str
    actions: list[dict] = []


# --- System prompt ---

SYSTEM_PROMPT = """You are an AI assistant for a Kanban board project management app.
The user will ask you questions or request changes to their board.

You will be given the current board state as JSON. When the user asks you to create, update, move, or delete cards, include the appropriate actions in your response.

Reply with valid JSON matching this schema:
{
  "reply": "Your conversational response to the user",
  "actions": [
    // Optional array of board actions. Omit or use [] if no changes needed.
    // Create a card:
    {"action": "create", "column_id": <int>, "title": "<string>", "details": "<string>"}
    // Update a card:
    {"action": "update", "card_id": <int>, "title": "<string or null>", "details": "<string or null>"}
    // Move a card:
    {"action": "move", "card_id": <int>, "column_id": <int>, "position": <int>}
    // Delete a card:
    {"action": "delete", "card_id": <int>}
  ]
}

Rules:
- Always respond with valid JSON only. No markdown fences, no extra text.
- column_id and card_id refer to the numeric IDs shown in the board state.
- position is 0-indexed within the target column.
- If the user just wants to chat, return an empty actions array.
"""


# --- Board loader ---


def load_board_json(user_id: int) -> dict | None:
    conn = get_connection()
    board = conn.execute(
        "SELECT id, title FROM boards WHERE user_id = ?", (user_id,)
    ).fetchone()
    if not board:
        conn.close()
        return None

    columns = conn.execute(
        "SELECT id, title, position FROM columns WHERE board_id = ? ORDER BY position",
        (board["id"],),
    ).fetchall()

    result_columns = []
    for col in columns:
        cards = conn.execute(
            "SELECT id, title, details, position FROM cards WHERE column_id = ? ORDER BY position",
            (col["id"],),
        ).fetchall()
        result_columns.append({
            "id": col["id"],
            "title": col["title"],
            "position": col["position"],
            "cards": [dict(c) for c in cards],
        })

    conn.close()
    return {"id": board["id"], "title": board["title"], "columns": result_columns}


# --- Parse and validate ---


def parse_ai_response(raw: str) -> AIResponse:
    """Parse raw AI text into a validated AIResponse."""
    # Strip markdown fences if model wraps in ```json
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    data = json.loads(text)
    return AIResponse(**data)


# --- Apply actions ---


def apply_actions(actions: list[dict]) -> list[str]:
    """Apply board actions and return a list of results/errors."""
    results = []
    conn = get_connection()
    try:
        for action_data in actions:
            action = action_data.get("action")
            try:
                if action == "create":
                    a = CardCreateAction(**action_data)
                    row = conn.execute(
                        "SELECT COALESCE(MAX(position), -1) + 1 as next_pos FROM cards WHERE column_id = ?",
                        (a.column_id,),
                    ).fetchone()
                    pos = row["next_pos"]
                    conn.execute(
                        "INSERT INTO cards (column_id, title, details, position) VALUES (?, ?, ?, ?)",
                        (a.column_id, a.title, a.details, pos),
                    )
                    results.append(f"Created card '{a.title}' in column {a.column_id}")

                elif action == "update":
                    a = CardUpdateAction(**action_data)
                    card = conn.execute("SELECT * FROM cards WHERE id = ?", (a.card_id,)).fetchone()
                    if not card:
                        results.append(f"Card {a.card_id} not found")
                        continue
                    title = a.title if a.title is not None else card["title"]
                    details = a.details if a.details is not None else card["details"]
                    conn.execute(
                        "UPDATE cards SET title = ?, details = ? WHERE id = ?",
                        (title, details, a.card_id),
                    )
                    results.append(f"Updated card {a.card_id}")

                elif action == "move":
                    a = CardMoveAction(**action_data)
                    card = conn.execute("SELECT column_id, position FROM cards WHERE id = ?", (a.card_id,)).fetchone()
                    if not card:
                        results.append(f"Card {a.card_id} not found")
                        continue
                    old_col = card["column_id"]
                    old_pos = card["position"]
                    conn.execute(
                        "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
                        (old_col, old_pos),
                    )
                    conn.execute(
                        "UPDATE cards SET position = position + 1 WHERE column_id = ? AND position >= ?",
                        (a.column_id, a.position),
                    )
                    conn.execute(
                        "UPDATE cards SET column_id = ?, position = ? WHERE id = ?",
                        (a.column_id, a.position, a.card_id),
                    )
                    results.append(f"Moved card {a.card_id} to column {a.column_id}")

                elif action == "delete":
                    a = CardDeleteAction(**action_data)
                    card = conn.execute("SELECT column_id, position FROM cards WHERE id = ?", (a.card_id,)).fetchone()
                    if not card:
                        results.append(f"Card {a.card_id} not found")
                        continue
                    conn.execute("DELETE FROM cards WHERE id = ?", (a.card_id,))
                    conn.execute(
                        "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
                        (card["column_id"], card["position"]),
                    )
                    results.append(f"Deleted card {a.card_id}")

                else:
                    results.append(f"Unknown action: {action}")

            except Exception as e:
                results.append(f"Error applying {action}: {e}")

        conn.commit()
    finally:
        conn.close()
    return results


# --- Main chat function ---


def chat_with_board(user_id: int, messages: list[dict[str, str]]) -> dict:
    """Send user messages + board context to AI, parse response, apply actions."""
    board = load_board_json(user_id)
    if board is None:
        return {"reply": "No board found for this user.", "actions_applied": []}

    system_content = SYSTEM_PROMPT + f"\n\nCurrent board state:\n{json.dumps(board, indent=2)}"
    full_messages = [{"role": "system", "content": system_content}] + messages

    raw_reply = chat(full_messages)
    ai_response = parse_ai_response(raw_reply)

    actions_applied = []
    if ai_response.actions:
        actions_applied = apply_actions(ai_response.actions)

    return {"reply": ai_response.reply, "actions_applied": actions_applied}
