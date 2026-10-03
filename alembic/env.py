import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# ----------------------------------------------------------------------
# 1. Project Path Setup
# ----------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# ----------------------------------------------------------------------
# 2. Config & Logging
# ----------------------------------------------------------------------
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ----------------------------------------------------------------------
# 3. Dynamic Database URL & Models Setup
# ----------------------------------------------------------------------
from config import Config
from app.extensions import db

# Import your models so db.metadata registers all tables for autogenerate
# from app.models import *  # Adjust to your models module/package if needed

db_url = Config.SQLALCHEMY_DATABASE_URI

# Ensure synchronous PostgreSQL driver (strip asyncpg if present, normalize postgres://)
if db_url:
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    config.set_main_option("sqlalchemy.url", db_url)

target_metadata = db.metadata

# ----------------------------------------------------------------------
# 4. Migration Runners
# ----------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()