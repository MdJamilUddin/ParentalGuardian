import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from .config.settings import settings

log = logging.getLogger(__name__)
_ROOT = Path(__file__).resolve().parent.parent


def alembic_config(url: str | None = None) -> Config:
    if not (_ROOT / "migrations" / "env.py").exists():
        raise RuntimeError(
            f"Alembic folder not found at {_ROOT / 'migrations'}. Make sure backend/migrations is committed and "
            "deployed (check with: git ls-files backend/migrations)."
        )
    cfg = Config(str(_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(_ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", (url or settings.DATABASE_URL).replace("%", "%%"))
    return cfg


def run_migrations(url: str | None = None) -> None:
    """Bring the database to the latest schema (called on startup unless AUTO_MIGRATE=false)."""
    url = url or settings.DATABASE_URL
    cfg = alembic_config(url)
    engine = create_engine(url)
    try:
        tables = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()
    if "parents" in tables and "alembic_version" not in tables:
        # a development database created before migrations existed: adopt it instead of recreating tables
        log.warning("Database has no migration history; marking it as up to date (stamp head).")
        command.stamp(cfg, "head")
    else:
        command.upgrade(cfg, "head")
