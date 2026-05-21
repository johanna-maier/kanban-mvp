import os
import sqlite3
from hashlib import scrypt
from pathlib import Path

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

_SCRYPT_N = 16384
_SCRYPT_R = 8
_SCRYPT_P = 1


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    h = scrypt(password.encode(), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
    return salt.hex() + "$" + h.hex()


def verify_password(password: str, stored: str) -> bool:
    salt_hex, hash_hex = stored.split("$", 1)
    salt = bytes.fromhex(salt_hex)
    h = scrypt(password.encode(), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
    return h.hex() == hash_hex


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

    row = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()
    if row["c"] == 0:
        pw_hash = hash_password("password")
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("user", pw_hash),
        )
        user_id = cursor.lastrowid
        board_cursor = conn.execute(
            "INSERT INTO boards (user_id, title) VALUES (?, 'My Board')", (user_id,)
        )
        board_id = board_cursor.lastrowid
        for i, title in enumerate(DEFAULT_COLUMNS):
            conn.execute(
                "INSERT INTO columns (board_id, title, position) VALUES (?, ?, ?)",
                (board_id, title, i),
            )
        conn.commit()
    conn.close()
