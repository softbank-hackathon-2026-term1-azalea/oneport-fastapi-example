from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from testcontainers.community.postgres import PostgresContainer

from app.core.config import get_settings


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    with PostgresContainer("postgres:17-alpine", driver="psycopg") as postgres:
        yield postgres.get_connection_url()


@pytest.fixture(scope="session", autouse=True)
def configure_env(database_url: str, monkeypatch_session: pytest.MonkeyPatch) -> None:
    monkeypatch_session.setenv("DATABASE_URL", database_url)
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
