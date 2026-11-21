from alembic import context
from sqlalchemy import create_engine, pool

from app.config.settings import settings
from app.models import entities  # noqa: F401
from app.models.db import Base

config = context.config
target_metadata = Base.metadata


def _url() -> str:
    # an explicit URL (tests, scripts) wins; otherwise use DATABASE_URL from the environment
    return config.get_main_option("sqlalchemy.url") or settings.DATABASE_URL


def run_migrations_offline():
    context.configure(url=_url(), target_metadata=target_metadata, literal_binds=True,
                      dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    engine = create_engine(_url(), poolclass=pool.NullPool)
    with engine.connect() as conn:
        context.configure(connection=conn, target_metadata=target_metadata,
                          render_as_batch=(conn.dialect.name == "sqlite"))
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
