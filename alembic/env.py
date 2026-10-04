import importlib
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, text

from app.core.config import get_settings
from app.core.db import Base

MIGRATION_LOCK_ID = 7_210_001

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

importlib.import_module("app.notes.models")
target_metadata = Base.metadata


def _database_url() -> str:
    return get_settings().sqlalchemy_url.render_as_string(hide_password=False)


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _database_url()
    connectable = engine_from_config(section, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            connection.execute(text("SELECT pg_advisory_xact_lock(:id)"), {"id": MIGRATION_LOCK_ID})
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
