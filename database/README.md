# Database

The schema is defined by the SQLAlchemy models (`backend/app/models/entities.py`) and created by Alembic migrations
(`backend/migrations/versions/`). The backend applies pending migrations automatically when it starts
(set `AUTO_MIGRATE=false` to do it by hand instead).

- Development: SQLite (default). Production: PostgreSQL, see `deployment/`.
- `retention.sql`: optional daily cleanup of data older than 30 days.

## Changing the schema
1. Edit the models.
2. `cd backend && alembic revision --autogenerate -m "describe the change"`
3. Read the generated file in `migrations/versions/` and fix anything odd (autogenerate is a draft).
4. `pytest -q` (a test fails if models and migrations disagree) and commit both files.
5. Deploy: the backend migrates on start. Take a backup first (`deployment/backup.sh`).

Useful commands (in `backend/`, venv active):

    alembic current                 # which migration the database is at
    alembic upgrade head            # apply all pending migrations
    alembic downgrade -1            # undo the last one
    alembic upgrade head --sql      # print the SQL instead of running it (a plain schema.sql for PostgreSQL)
    alembic stamp head              # mark an existing database as up to date without changing it

Rules for production: never edit a migration that was already deployed (add a new one); avoid destructive
changes (dropping or renaming columns) in a single step; always back up before deploying a migration.
