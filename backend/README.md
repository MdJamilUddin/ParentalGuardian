# ParentalGuardian backend (FastAPI)

    cd backend
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    export SECRET_KEY="$(python -c 'import secrets;print(secrets.token_hex(32))')"
    uvicorn app.main:app --reload

Docs: http://localhost:8000/docs

## Flow
1. Parent: POST /auth/register -> token
2. Parent: POST /children, then POST /children/{id}/pairing-code (6 digits, 10 min, single use)
3. Child app: POST /device/pair {code, device_name} -> device_token (store securely)
4. Child app: POST /device/sync with Bearer device_token (batches of locations, usage, battery)
5. Parent: GET /children/{id}/location/latest | /locations | /usage | /battery
6. Parent: DELETE /devices/{id} revokes a device

Env: DATABASE_URL (PostgreSQL in production), SECRET_KEY (required in production),
RETENTION_DAYS (default 30), CORS_ORIGINS.

## Tests
    pip install -r requirements-dev.txt
    pytest -q
Tests use a temporary SQLite database and never touch `guardian.db`. They run automatically on GitHub via
`.github/workflows/backend-tests.yml`.

## Database migrations
Tables are created and updated by Alembic (`migrations/`). The app runs `alembic upgrade head` on startup;
set `AUTO_MIGRATE=false` to disable. An old development `guardian.db` created before migrations existed is
adopted automatically. After changing a model run `alembic revision --autogenerate -m "message"`.
See `../database/README.md`.

## Push notifications
Parents get alerts when a phone stops reporting (2 h) or its battery is low (15%). Needs a Firebase project, see
`../deployment/FIREBASE.md`. Without credentials the backend runs normally and just logs the alerts it would send.
