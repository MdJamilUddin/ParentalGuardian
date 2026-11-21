# ParentalGuardian

A family safety system: the child's Android phone shares location, app usage time and battery level with the
parent, who views it in an Android app or a web dashboard. The child app is visible and shows a permanent
notification while active.

    backend/         FastAPI API (auth, pairing, sync, reports), rate limits, retention
    database/        PostgreSQL schema, retention SQL, Alembic notes
    child-android/   Kotlin app: pairing, location, battery, usage, offline queue, sync
    parent-android/  Kotlin app: login, children, map, usage, battery, pairing codes
    parent-web/      Browser dashboard (same features)
    deployment/      Docker Compose + Caddy (HTTPS), server setup script, backups, monitoring (STAGING.md, MONITORING.md)

## Run locally (development)
1. Backend: see `backend/README.md` (SQLite, no setup). API docs at http://localhost:8000/docs
2. Dashboard: `cd parent-web/dashboard && python3 -m http.server 5173`, open http://localhost:5173
3. Android apps: open `child-android` and `parent-android` in Android Studio, run on the emulator.
   Debug builds talk to `http://10.0.2.2:8000`.
4. Parent: create an account, add a child, "Add a phone" -> 6-digit code -> enter it in the child app.

## Go live
See `deployment/README.md`.
