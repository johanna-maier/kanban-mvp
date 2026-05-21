def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_login_success(client):
    r = client.post("/api/login", json={"username": "user", "password": "password"})
    assert r.status_code == 200
    data = r.json()
    assert data["user_id"] == 1
    assert data["username"] == "user"


def test_login_invalid(client):
    r = client.post("/api/login", json={"username": "user", "password": "wrong"})
    assert r.status_code == 401


def test_get_board(client):
    r = client.get("/api/board/1")
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "My Board"
    assert len(data["columns"]) == 5
    assert data["columns"][0]["title"] == "Backlog"


def test_get_board_not_found(client):
    r = client.get("/api/board/999")
    assert r.status_code == 404


def test_rename_column(client):
    r = client.put("/api/columns/1", json={"title": "New Name"})
    assert r.status_code == 200
    assert r.json()["title"] == "New Name"

    # Verify persisted
    board = client.get("/api/board/1").json()
    assert board["columns"][0]["title"] == "New Name"


def test_rename_column_not_found(client):
    r = client.put("/api/columns/9999", json={"title": "Ghost"})
    assert r.status_code == 404


def test_create_card(client):
    r = client.post("/api/columns/1/cards", json={"title": "Test card", "details": "Some details"})
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "Test card"
    assert data["details"] == "Some details"
    assert "id" in data

    # Verify in board
    board = client.get("/api/board/1").json()
    cards = board["columns"][0]["cards"]
    assert any(c["title"] == "Test card" for c in cards)


def test_update_card(client):
    # Create a card first
    create = client.post("/api/columns/1/cards", json={"title": "Original"})
    card_id = create.json()["id"]

    r = client.put(f"/api/cards/{card_id}", json={"title": "Updated"})
    assert r.status_code == 200
    assert r.json()["title"] == "Updated"


def test_update_card_not_found(client):
    r = client.put("/api/cards/999", json={"title": "X"})
    assert r.status_code == 404


def test_delete_card(client):
    create = client.post("/api/columns/1/cards", json={"title": "To delete"})
    card_id = create.json()["id"]

    r = client.delete(f"/api/cards/{card_id}")
    assert r.status_code == 200

    # Verify gone
    board = client.get("/api/board/1").json()
    cards = board["columns"][0]["cards"]
    assert not any(c["id"] == card_id for c in cards)


def test_delete_card_not_found(client):
    r = client.delete("/api/cards/999")
    assert r.status_code == 404


def test_move_card(client):
    # Create card in column 1
    create = client.post("/api/columns/1/cards", json={"title": "Mover"})
    card_id = create.json()["id"]

    # Move to column 2 at position 0
    r = client.put(f"/api/cards/{card_id}/move", json={"column_id": 2, "position": 0})
    assert r.status_code == 200

    # Verify it's in column 2
    board = client.get("/api/board/1").json()
    col2_cards = board["columns"][1]["cards"]
    assert any(c["id"] == card_id for c in col2_cards)


def test_move_card_not_found(client):
    r = client.put("/api/cards/999/move", json={"column_id": 1, "position": 0})
    assert r.status_code == 404
