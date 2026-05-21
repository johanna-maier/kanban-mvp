import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import database


@pytest.fixture(autouse=True)
def tmp_db(monkeypatch, tmp_path):
    """Use a temporary database for each test."""
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.init_db(db_path)
    yield db_path


@pytest.fixture
def client(tmp_db):
    from backend.app.main import app
    return TestClient(app)
