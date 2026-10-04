import logging
import os
import sys
import time

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.release import project_version

log = logging.getLogger(__name__)


def wait_for_database(timeout_seconds: float, interval_seconds: float = 2.0) -> None:
    settings = get_settings()
    engine = create_engine(settings.sqlalchemy_url, pool_pre_ping=True)
    deadline = time.monotonic() + timeout_seconds
    attempt = 0
    try:
        while True:
            attempt += 1
            try:
                with engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
                log.info("database reachable", extra={"attempt": attempt})
                return
            except OperationalError as exc:
                if time.monotonic() >= deadline:
                    log.error(
                        "database not reachable", extra={"attempt": attempt, "error": str(exc)}
                    )
                    raise
                log.warning("database not ready, retrying", extra={"attempt": attempt})
                time.sleep(interval_seconds)
    finally:
        engine.dispose()


def migrate(config: Config) -> bool:
    script = ScriptDirectory.from_config(config)
    known = {revision.revision for revision in script.walk_revisions()}
    engine = create_engine(get_settings().sqlalchemy_url)
    try:
        with engine.connect() as connection:
            current = set(MigrationContext.configure(connection).get_current_heads())
    finally:
        engine.dispose()

    unknown = current - known
    if unknown:
        log.warning(
            "database schema is newer than this release, skipping migrations",
            extra={
                "database_revisions": sorted(current),
                "release_head": script.get_current_head(),
            },
        )
        return False

    command.upgrade(config, "head")
    log.info("migrations applied", extra={"release_head": script.get_current_head()})
    return True


def main() -> None:
    settings = get_settings()
    configure_logging(
        fmt=settings.log_format,
        level=settings.log_level,
        static_fields={"app": settings.app_name, "version": project_version()},
    )
    wait_for_database(timeout_seconds=float(os.environ.get("DB_WAIT_SECONDS", "60")))
    migrate(Config("alembic.ini"))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("prestart failed")
        sys.exit(1)
