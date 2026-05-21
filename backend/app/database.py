import sqlite3
from pathlib import Path
from hashlib import sha256

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "kanban.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS boards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title TEXT NOT NULL DEFAULT 'My Board'
);

CREATE TABLE IF NOT EXISTS columns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    board_id INTEGER NOT NULL REFERENCES boards(id),
    title TEXT NOT NULL,
    position INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    column_id INTEGER NOT NULL REFERENCES columns(id),
    title TEXT NOT NULL,
    details TEXT NOT NULL DEFAULT '',
    position INTEGER NOT NULL
);
"""

DEFAULT_COLUMNS = ["Backlog", "Discovery", "In Progress", "Review", "Done"]


def hash_password(password: str) -> str:
    return sha256(password.encode()).hexdigest()


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path if db_path is not None else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path | None = None) -> None:
    conn = get_connection(db_path)
    conn.executescript(SCHEMA_SQL)

    # Seed default user and board if empty
    row = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()
    if row["c"] == 0:
        pw_hash = hash_password("password")
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("user", pw_hash),
        )
        conn.execute(
            "INSERT INTO boards (user_id, title) VALUES (1, 'My Board')"
        )
        for i, title in enumerate(DEFAULT_COLUMNS):
            conn.execute(
                "INSERT INTO columns (board_id, title, position) VALUES (1, ?, ?)",
                (title, i),
            )
        conn.commit()
    conn.close()
