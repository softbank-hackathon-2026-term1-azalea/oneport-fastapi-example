from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.release import project_version
from app.main import app


def test_health_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_forced_unhealthy(client: TestClient) -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(app_force_unhealthy=True)
    try:
        response = client.get("/health")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
    assert response.json()["reason"] == "APP_FORCE_UNHEALTHY"


def test_ready_checks_database(client: TestClient) -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}


def test_version_exposes_release_info(client: TestClient) -> None:
    body = client.get("/version").json()
    assert body["app"] == "notes"
    assert body["version"] == project_version() == "1.1.1"
    assert set(body) == {"app", "version", "git_sha", "built_at", "color", "hostname", "started_at"}


def test_failure_always_503(client: TestClient) -> None:
    assert client.get("/failure").status_code == 503


def test_request_id_header_is_echoed(client: TestClient) -> None:
    request_id = "2b1c0b8e-7d3a-4f1e-9c0a-5f6d7e8a9b0c"
    response = client.get("/version", headers={"X-Request-ID": request_id})
    assert response.headers["X-Request-ID"] == request_id

    response = client.get("/version", headers={"X-Request-ID": "not-a-uuid"})
    assert response.headers["X-Request-ID"] != "not-a-uuid"
    assert len(response.headers["X-Request-ID"]) == 32


def test_index_serves_page(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Oneport Notes" in response.text
