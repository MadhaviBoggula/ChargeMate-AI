"""Alembic environment wired to app settings (reads the root .env)."""
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make backend/ importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings  # noqa: E402
from app.database.base import Base  # noqa: E402

config = context.config
settings = get_settings()

_default_url = config.get_main_option("sqlalchemy.url")
if not _default_url:
    _default_url = settings.database_url
# Normalize to the psycopg 3 dialect
for _prefix in ("postgresql://", "postgres://"):
    if _default_url.startswith(_prefix):
        _default_url = _default_url.replace(_prefix, "postgresql+psycopg://", 1)
config.set_main_option("sqlalchemy.url", _default_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Domain models register tables here as members add them:
# from app.models import users, stations, ...  # noqa: F401
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
