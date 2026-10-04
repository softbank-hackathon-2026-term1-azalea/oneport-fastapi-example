from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def test_visits_start_at_zero(client: TestClient) -> None:
    response = client.get("/visits")
    assert response.status_code == 200
    assert response.json() == {"visits": 0}


def test_record_visit_increments_counter(client: TestClient) -> None:
    assert client.post("/visits").json() == {"visits": 1}
    assert client.post("/visits").json() == {"visits": 2}
    assert client.get("/visits").json() == {"visits": 2}


def test_ready_reports_cache(client: TestClient) -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up", "cache": "up"}


@pytest.fixture
def client_without_cache(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.delenv("REDIS_URL")
    get_settings.cache_clear()
    try:
        with TestClient(create_app()) as test_client:
            yield test_client
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()


def test_visits_unavailable_without_cache(client_without_cache: TestClient) -> None:
    response = client_without_cache.post("/visits")
    assert response.status_code == 503
    assert response.json() == {"detail": "cache is not configured"}


def test_ready_without_cache(client_without_cache: TestClient) -> None:
    response = client_without_cache.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up", "cache": "disabled"}


@pytest.fixture
def client_with_unreachable_cache(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:1/0")
    get_settings.cache_clear()
    try:
        with TestClient(create_app()) as test_client:
            yield test_client
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()


def test_unreachable_cache_returns_503(client_with_unreachable_cache: TestClient) -> None:
    assert client_with_unreachable_cache.post("/visits").json() == {"detail": "cache unavailable"}
    response = client_with_unreachable_cache.get("/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "up", "cache": "down"}
