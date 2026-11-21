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
