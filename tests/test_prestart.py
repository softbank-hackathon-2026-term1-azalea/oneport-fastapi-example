from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

from app.prestart import migrate


def _set_revision(database_url: str, revision: str) -> None:
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(text("UPDATE alembic_version SET version_num = :rev"), {"rev": revision})
    engine.dispose()


def test_migrate_applies_pending_revisions() -> None:
    config = Config("alembic.ini")
    command.downgrade(config, "base")
    command.upgrade(config, "0001")

    assert migrate(config) is True


def test_migrate_skips_when_database_is_newer_than_release(database_url: str) -> None:
    head = ScriptDirectory.from_config(Config("alembic.ini")).get_current_head()
    assert head is not None
    _set_revision(database_url, "9999")
    try:
        assert migrate(Config("alembic.ini")) is False
    finally:
        _set_revision(database_url, head)
