from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from redis import Redis
from sqlalchemy import create_engine, text
from testcontainers.community.postgres import PostgresContainer
from testcontainers.community.valkey import ValkeyContainer

from app.core.config import get_settings


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    with PostgresContainer("postgres:17-alpine", driver="psycopg") as postgres:
        yield postgres.get_connection_url()


@pytest.fixture(scope="session")
def redis_url() -> Iterator[str]:
    with ValkeyContainer("valkey/valkey:8-alpine") as valkey:
        yield f"redis://{valkey.get_container_host_ip()}:{valkey.get_exposed_port()}/0"


@pytest.fixture(scope="session", autouse=True)
def configure_env(
    database_url: str, redis_url: str, monkeypatch_session: pytest.MonkeyPatch
) -> None:
    monkeypatch_session.setenv("DATABASE_URL", database_url)
    monkeypatch_session.setenv("REDIS_URL", redis_url)
    monkeypatch_session.setenv("LOG_FORMAT", "text")
    monkeypatch_session.delenv("APP_FORCE_UNHEALTHY", raising=False)
    get_settings.cache_clear()


@pytest.fixture(scope="session")
def monkeypatch_session() -> Iterator[pytest.MonkeyPatch]:
    patch = pytest.MonkeyPatch()
    yield patch
    patch.undo()


@pytest.fixture(scope="session", autouse=True)
def migrated(configure_env: None) -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture(scope="session")
def client(migrated: None) -> Iterator[TestClient]:
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clean_tables(database_url: str, migrated: None) -> None:
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE notes RESTART IDENTITY"))
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_cache(redis_url: str) -> None:
    with Redis.from_url(redis_url) as redis:
        redis.flushdb()
