from fastapi.testclient import TestClient

from app.core.config import get_settings


def test_release_header_is_absent_without_release_id(client: TestClient) -> None:
    assert "X-Launchpad-Release" not in client.get("/health").headers


def test_release_header_echoes_release_id(client: TestClient) -> None:
    settings = get_settings()
    settings.launchpad_release_id = "rel-123"
    try:
        for path in ("/health", "/version", "/notes"):
            assert client.get(path).headers["X-Launchpad-Release"] == "rel-123"
    finally:
        settings.launchpad_release_id = None
