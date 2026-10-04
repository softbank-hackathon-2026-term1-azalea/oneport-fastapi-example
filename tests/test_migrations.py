from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def _columns(database_url: str) -> set[str]:
    engine = create_engine(database_url)
    try:
        return {column["name"] for column in inspect(engine).get_columns("notes")}
    finally:
        engine.dispose()


def test_migrations_are_reversible(database_url: str) -> None:
    config = Config("alembic.ini")
    assert "done" in _columns(database_url)

    command.downgrade(config, "0001")
    assert "done" not in _columns(database_url)

    command.upgrade(config, "head")
    assert "done" in _columns(database_url)
