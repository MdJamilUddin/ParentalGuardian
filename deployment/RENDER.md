# Staging on Render (hosted platform, no server to administer)

Render runs the backend from your GitHub repository and provides PostgreSQL and HTTPS. Free plans exist, but check
Render's current free-tier limits: free web services may sleep when idle (the first request after a pause is
slow) and free databases may be limited or expire. That is fine for testing, not for real families.

## 1. Put the project on GitHub (private repo), see the main instructions.
Check that `backend/migrations/` and `backend/app/` are both in the repository (open them on github.com).

## 2. Create the database
Render dashboard, New, PostgreSQL. Name it `guardian-db`, then copy its **Internal Database URL**.

## 3. Create the backend service
New, Web Service, connect the repository, then:

| Setting | Value |
|---|---|
| Root Directory | `backend` |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips="*"` |
| Health Check Path | `/health/ready` |
| Instances | 1 (the login rate limiter is per process) |

Environment variables:

| Key | Value |
|---|---|
| `PYTHON_VERSION` | `3.12.8` (a fully qualified version; Render's default may be too new for some libraries) |
| `DATABASE_URL` | the Internal Database URL from step 2 |
| `SECRET_KEY` | random: `py -c "import secrets;print(secrets.token_hex(32))"` |
| `ENVIRONMENT` | `staging` |
| `LOG_JSON` | `true` |
| `ACCESS_TOKEN_MINUTES` | `1440` |
| `CORS_ORIGINS` | the addresses the dashboard is opened from, comma separated, e.g. `http://localhost:5173` |

Deploy. The backend creates its tables itself on start (migrations). Check `https://YOUR-SERVICE.onrender.com/health/ready`
(should show ok) and `https://YOUR-SERVICE.onrender.com/docs`.

## 4. Use it
- **Dashboard from your PC:** in `parent-web/dashboard/config.js` set `window.GUARDIAN_API = "https://YOUR-SERVICE.onrender.com";`
  and serve it with `py -m http.server 5173` (keep `http://localhost:5173` in `CORS_ORIGINS`).
- **Android apps:** set the `staging` build type's `BASE_URL` to `https://YOUR-SERVICE.onrender.com` (no `/api` here,
  that prefix only exists in the Docker/Caddy setup), then pick the `staging` build variant.

## Troubleshooting
| Log message | Cause and fix |
|---|---|
| `Alembic folder not found` / `Path doesn't exist ... migrations` | `backend/migrations` is not in the repository. Commit and push it, redeploy. |
| `No module named psycopg2` | `psycopg2-binary` missing from `requirements.txt`; use the current file. |
| `Can't load plugin: sqlalchemy.dialects:postgres` | `DATABASE_URL` starts with `postgres://`; the current code converts it, make sure you deployed the latest version. |
| Build fails compiling a package | Set `PYTHON_VERSION` to `3.12.8`. |
| Dashboard login fails with a CORS error in the browser console | Add the dashboard's address to `CORS_ORIGINS` and redeploy. |
