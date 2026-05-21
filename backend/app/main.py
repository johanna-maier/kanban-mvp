from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.app.database import get_connection, init_db, hash_password


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)


# --- Models ---


class LoginRequest(BaseModel):
    username: str
    password: str


class CardCreate(BaseModel):
    title: str
    details: str = ""


class CardUpdate(BaseModel):
    title: str | None = None
    details: str | None = None


class CardMove(BaseModel):
    column_id: int
    position: int


class ColumnRename(BaseModel):
    title: str


# --- Auth ---


@app.post("/api/login")
def login(body: LoginRequest) -> dict[str, object]:
    conn = get_connection()
    row = conn.execute(
        "SELECT id, password_hash FROM users WHERE username = ?",
        (body.username,),
    ).fetchone()
    conn.close()
    if not row or row["password_hash"] != hash_password(body.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"user_id": row["id"], "username": body.username}


# --- Health ---


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# --- Board ---


@app.get("/api/board/{user_id}")
def get_board(user_id: int) -> dict[str, object]:
    conn = get_connection()
    board = conn.execute(
        "SELECT id, title FROM boards WHERE user_id = ?", (user_id,)
    ).fetchone()
    if not board:
        conn.close()
        raise HTTPException(status_code=404, detail="Board not found")

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


# --- Columns ---


@app.put("/api/columns/{column_id}")
def rename_column(column_id: int, body: ColumnRename) -> dict[str, object]:
    conn = get_connection()
    conn.execute(
        "UPDATE columns SET title = ? WHERE id = ?", (body.title, column_id)
    )
    conn.commit()
    conn.close()
    return {"id": column_id, "title": body.title}


# --- Cards ---


@app.post("/api/columns/{column_id}/cards")
def create_card(column_id: int, body: CardCreate) -> dict[str, object]:
    conn = get_connection()
    # Get next position
    row = conn.execute(
        "SELECT COALESCE(MAX(position), -1) + 1 as next_pos FROM cards WHERE column_id = ?",
        (column_id,),
    ).fetchone()
    pos = row["next_pos"]
    cursor = conn.execute(
        "INSERT INTO cards (column_id, title, details, position) VALUES (?, ?, ?, ?)",
        (column_id, body.title, body.details, pos),
    )
    conn.commit()
    card_id = cursor.lastrowid
    conn.close()
    return {"id": card_id, "title": body.title, "details": body.details, "position": pos}


@app.put("/api/cards/{card_id}")
def update_card(card_id: int, body: CardUpdate) -> dict[str, object]:
    conn = get_connection()
    card = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    if not card:
        conn.close()
        raise HTTPException(status_code=404, detail="Card not found")

    title = body.title if body.title is not None else card["title"]
    details = body.details if body.details is not None else card["details"]
    conn.execute(
        "UPDATE cards SET title = ?, details = ? WHERE id = ?",
        (title, details, card_id),
    )
    conn.commit()
    conn.close()
    return {"id": card_id, "title": title, "details": details}


@app.put("/api/cards/{card_id}/move")
def move_card(card_id: int, body: CardMove) -> dict[str, str]:
    conn = get_connection()
    card = conn.execute("SELECT column_id, position FROM cards WHERE id = ?", (card_id,)).fetchone()
    if not card:
        conn.close()
        raise HTTPException(status_code=404, detail="Card not found")

    old_column_id = card["column_id"]
    old_position = card["position"]

    # Remove from old position
    conn.execute(
        "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
        (old_column_id, old_position),
    )

    # Make space in target column
    conn.execute(
        "UPDATE cards SET position = position + 1 WHERE column_id = ? AND position >= ?",
        (body.column_id, body.position),
    )

    # Place card
    conn.execute(
        "UPDATE cards SET column_id = ?, position = ? WHERE id = ?",
        (body.column_id, body.position, card_id),
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}


@app.delete("/api/cards/{card_id}")
def delete_card(card_id: int) -> dict[str, str]:
    conn = get_connection()
    card = conn.execute("SELECT column_id, position FROM cards WHERE id = ?", (card_id,)).fetchone()
    if not card:
        conn.close()
        raise HTTPException(status_code=404, detail="Card not found")

    conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    conn.execute(
        "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
        (card["column_id"], card["position"]),
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}


static_dir = Path(__file__).resolve().parent / "static"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
