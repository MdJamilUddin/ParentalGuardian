from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from app.migrate import alembic_config, run_migrations
from app.models import entities  # noqa: F401
from app.models.db import Base


def test_migrations_match_the_models(tmp_path):
    """If this fails you changed a model without creating a migration (alembic revision --autogenerate)."""
    url = f"sqlite:///{tmp_path / 'm.db'}"
    run_migrations(url)
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    finally:
        engine.dispose()
    assert diff == []


def test_downgrade_removes_everything(tmp_path):
    url = f"sqlite:///{tmp_path / 'm.db'}"
    run_migrations(url)
    command.downgrade(alembic_config(url), "base")
    engine = create_engine(url)
    try:
        assert set(inspect(engine).get_table_names()) <= {"alembic_version"}
    finally:
        engine.dispose()


def test_unversioned_dev_database_is_adopted(tmp_path):
    url = f"sqlite:///{tmp_path / 'legacy.db'}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)  # how the old version of the backend created it
    engine.dispose()
    run_migrations(url)  # must not fail with "table already exists"
    engine = create_engine(url)
    try:
        assert "alembic_version" in inspect(engine).get_table_names()
    finally:
        engine.dispose()
