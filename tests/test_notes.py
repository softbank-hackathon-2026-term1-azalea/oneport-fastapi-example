from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text


def test_create_and_list_notes(client: TestClient) -> None:
    first = client.post("/notes", json={"title": "first"})
    second = client.post("/notes", json={"title": "  second  "})
    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["title"] == "second"

    notes = client.get("/notes").json()
    assert [note["title"] for note in notes] == ["second", "first"]
    assert all(set(note) == {"id", "title", "created_at", "done"} for note in notes)


def test_blank_title_is_rejected(client: TestClient) -> None:
    assert client.post("/notes", json={"title": "   "}).status_code == 422
    assert client.post("/notes", json={"title": ""}).status_code == 422
    assert client.post("/notes", json={}).status_code == 422


def test_title_longer_than_200_is_rejected(client: TestClient) -> None:
    assert client.post("/notes", json={"title": "x" * 201}).status_code == 422
    assert client.post("/notes", json={"title": "x" * 200}).status_code == 201


def test_delete_note(client: TestClient) -> None:
    note_id = client.post("/notes", json={"title": "to delete"}).json()["id"]
    assert client.delete(f"/notes/{note_id}").status_code == 204
    assert client.get("/notes").json() == []


def test_delete_missing_note_returns_404(client: TestClient) -> None:
    response = client.delete("/notes/999999")
    assert response.status_code == 404
    assert response.json()["note_id"] == 999999


def test_list_limit_is_validated(client: TestClient) -> None:
    assert client.get("/notes", params={"limit": 0}).status_code == 422
    assert client.get("/notes", params={"limit": 201}).status_code == 422


def test_new_note_is_not_done(client: TestClient) -> None:
    assert client.post("/notes", json={"title": "fresh"}).json()["done"] is False


def test_patch_toggles_done(client: TestClient) -> None:
    note_id = client.post("/notes", json={"title": "toggle"}).json()["id"]

    response = client.patch(f"/notes/{note_id}", json={"done": True})
    assert response.status_code == 200
    assert response.json()["done"] is True
    assert client.get("/notes").json()[0]["done"] is True

    assert client.patch(f"/notes/{note_id}", json={"done": False}).json()["done"] is False


def test_patch_missing_note_returns_404(client: TestClient) -> None:
    response = client.patch("/notes/999999", json={"done": True})
    assert response.status_code == 404
    assert response.json()["note_id"] == 999999


def test_patch_requires_boolean(client: TestClient) -> None:
    note_id = client.post("/notes", json={"title": "strict"}).json()["id"]
    assert client.patch(f"/notes/{note_id}", json={"done": "yes"}).status_code == 422
    assert client.patch(f"/notes/{note_id}", json={}).status_code == 422


def test_row_written_by_previous_release_reads_as_not_done(
    client: TestClient, database_url: str
) -> None:
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO notes (title) VALUES ('from 1.0.0')"))
    engine.dispose()

    notes = client.get("/notes").json()
    assert notes[0]["title"] == "from 1.0.0"
    assert notes[0]["done"] is False
