# Deployment (Docker Compose: PostgreSQL + FastAPI + Caddy with automatic HTTPS)

New to this? Follow **STAGING.md** (server setup from zero) and **MONITORING.md** (alerts, logs, error tracking).
This page is the short reference.

One domain serves everything:
- `https://DOMAIN/`      parent web dashboard
- `https://DOMAIN/api/`  backend API (used by both Android apps and the dashboard)

## 1. Prepare
- A server with Docker and Docker Compose (a small VPS is enough), ports 80 and 443 open.
- A domain with a DNS A record pointing to the server's public IP.

## 2. Configure and start
    cd deployment
    cp .env.example .env
    # edit .env: DOMAIN, and put the output of `openssl rand -hex 32` into DB_PASSWORD and SECRET_KEY
    docker compose up -d --build
    docker compose logs -f backend

Open https://DOMAIN, create a parent account, add a child.
To test on your own computer first, use `DOMAIN=localhost` (Caddy makes a local certificate; your browser will warn).

## 3. Point the apps at the server
In `child-android/app/build.gradle.kts` and `parent-android/app/build.gradle.kts`, set the **release**
`BASE_URL` to `https://DOMAIN/api`, then build signed release APKs/AABs in Android Studio.

## 4. Backups and cleanup
- Backups: add `backup.sh` to cron (see the file). Copy the `backups/` folder off the server regularly.
- Old data is purged when the backend starts (RETENTION_DAYS). For a daily purge add to cron:
      0 3 * * * cd /path/to/ParentalGuardian/deployment && docker compose exec -T db psql -U guardian guardian < ../database/retention.sql
- Update: take a backup (`./backup.sh`), copy the new files, then `docker compose up -d --build`.
  Database migrations are applied automatically when the backend starts (check `docker compose logs backend`).

## 5. Go-live checklist
- [ ] HTTPS works and http:// redirects to https://
- [ ] `SECRET_KEY` and `DB_PASSWORD` are random and only in `.env`
- [ ] A test child phone pairs, and location, usage and battery show in the dashboard and the parent app
- [ ] Disconnecting a phone from the dashboard makes the child app return to the pairing screen
- [ ] A backup was made and a restore was tested once
- [ ] Release APKs are signed and use the HTTPS `BASE_URL`
- [ ] Children know the app is installed (it shows a permanent notification by design)
- [ ] If publishing on Google Play: privacy policy, Data safety form, background location declaration

## If you can't open ports (home/laptop connection, shared IP)
Many ISPs share one public IP between customers, so port forwarding won't work. Options: rent a small VPS and
deploy there (simplest), or use a tunnel such as Cloudflare Tunnel in front of the `web` service
(then Caddy can listen on plain HTTP; remove the `{$DOMAIN}` HTTPS behavior by using `http://{$DOMAIN}` in the Caddyfile).

## Not included yet
Push notifications/alerts, geofences, refresh tokens, and multi-process rate limiting (the current limiter is
per-process, which is correct for this single-container setup).
