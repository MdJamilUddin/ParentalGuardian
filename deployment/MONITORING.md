# Monitoring and alerts

Three layers, from "is the server alive" to "is a child's phone reporting".

## 1. The server (you, the operator)

**Health endpoints**
- `/api/health`: the backend process is up.
- `/api/health/ready`: the backend can also reach the database (returns 503 if not). Docker uses this for its own
  healthcheck and restarts nothing by itself, but `docker compose ps` shows `healthy` or `unhealthy`.

**Watchdog and phone alerts (`monitor.sh`)**: every 5 minutes it checks the API, the dashboard, the three
containers, disk space (alerts above 85%) and the age of the last backup (alerts after 36 hours). It stays silent
when everything is fine, repeats an unresolved alert at most every 6 hours and sends one "Recovered" message.
1. Install the free **ntfy** app on your phone and subscribe to a topic with a long random name (anyone who knows
   the name can read it, so make it unguessable), for example `guardian-7f3k9x2q8w4m`.
2. In `deployment/.env` set `ALERT_URL=https://ntfy.sh/guardian-7f3k9x2q8w4m`.
3. Add the cron line from `crontab.example`. Test: `docker compose stop backend`, wait for the next run, then
   `docker compose start backend`.

**External uptime check (recommended)**: `monitor.sh` runs on the server it watches, so it can't tell you the
whole server is down. Add a free account at an uptime service (UptimeRobot, Better Stack and similar) that requests
`https://DOMAIN/api/health/ready` every few minutes and emails or messages you when it fails.

## 2. Errors and logs

**Logs**: the backend writes one JSON line per request (method, path, status, duration, request id; never
passwords, tokens or location data) plus warnings for failed logins, rejected device tokens and rate-limit hits.

    docker compose logs -f backend                         # live
    docker compose logs --since 1h backend | grep '"level": "WARNING"'
    docker compose logs backend | grep '"status": 5'       # server errors

Every response has an `X-Request-ID` header; a user who reports a problem can give you that id to find the request.
Docker rotates the logs (3 files of 10 MB) so they cannot fill the disk. Many "login failed" or "rate limit hit"
lines from one IP means someone is guessing passwords or pairing codes.

**Error tracking (optional)**: create a free project at sentry.io (type: FastAPI/Python), copy its DSN into
`SENTRY_DSN` in `.env` and run `docker compose up -d`. Unhandled errors then arrive with a stack trace. Personal
data is not attached. For the Android apps, add the Sentry or Firebase Crashlytics SDK before the public release so
you see crashes on real phones.

## 3. The children's phones

**In the apps**: the parent dashboard and the parent app show a yellow warning when a connected phone has not
reported for 2 hours (switched off, offline, app stopped, permission removed, or the phone brand killed the app in
the background).

**On the server**: devices that have gone quiet (run inside the database container):

    docker compose exec db psql -U guardian guardian -c "
      SELECT d.id, c.name AS child, d.name AS phone, d.last_seen
      FROM devices d JOIN children c ON c.id = d.child_id
      WHERE NOT d.revoked AND (d.last_seen IS NULL OR d.last_seen < now() AT TIME ZONE 'utc' - interval '6 hours')
      ORDER BY d.last_seen NULLS FIRST;"

Rows received per day (is data flowing?):

    docker compose exec db psql -U guardian guardian -c "
      SELECT date_trunc('day', recorded_at) AS day, count(*) FROM location_points
      GROUP BY 1 ORDER BY 1 DESC LIMIT 7;"

If many phones of one brand go quiet, it is almost always battery optimization on that brand: ask the family to set
the app to "Unrestricted battery" and enable autostart.

## Not included yet
Push notifications to the parent (needs Firebase Cloud Messaging), email alerts, metrics dashboards
(Prometheus/Grafana). The monitoring above is enough for a pilot; add those when you have many users.
