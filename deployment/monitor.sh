#!/usr/bin/env bash
# Health watchdog. Run every 5 minutes from cron (see crontab.example). Silent when everything is fine.
# When something is wrong it prints the problems and, if ALERT_URL is set in .env, POSTs them there
# (works with ntfy.sh, which pushes to your phone). Repeats at most every 6 hours; sends "recovered" once.
set -u
cd "$(dirname "$0")"
if [ -f .env ]; then set -a; . ./.env; set +a; fi
: "${DOMAIN:?DOMAIN missing in .env}"
ALERT_URL="${ALERT_URL:-}"
STATE=/tmp/guardian-monitor.state

send() {
  echo "$1"
  if [ -n "$ALERT_URL" ]; then
    curl -fsS --max-time 10 -H "Title: ParentalGuardian $DOMAIN" -d "$1" "$ALERT_URL" >/dev/null 2>&1 || true
  fi
}

problems=()
curl -fsS --max-time 10 -o /dev/null "https://$DOMAIN/api/health/ready" || problems+=("API not healthy: https://$DOMAIN/api/health/ready")
curl -fsS --max-time 10 -o /dev/null "https://$DOMAIN/" || problems+=("Dashboard not reachable: https://$DOMAIN/")

for svc in db backend web; do
  state=$(docker compose ps --format '{{.Service}} {{.State}}' 2>/dev/null | awk -v s="$svc" '$1==s {print $2}')
  [ "$state" = "running" ] || problems+=("container $svc is ${state:-missing}")
done

disk=$(df --output=pcent / | tail -1 | tr -dc '0-9')
[ "${disk:-0}" -lt 85 ] || problems+=("disk is ${disk}% full")

latest=$(ls -t backups/guardian-*.sql.gz 2>/dev/null | head -1)
if [ -z "$latest" ] || [ $(( $(date +%s) - $(stat -c %Y "$latest") )) -gt 129600 ]; then
  problems+=("no database backup in the last 36 hours")
fi

if [ ${#problems[@]} -eq 0 ]; then
  if [ -f "$STATE" ]; then rm -f "$STATE"; send "Recovered: all checks pass"; fi
  exit 0
fi

msg=$(printf -- '- %s\n' "${problems[@]}")
sig=$(printf '%s' "$msg" | md5sum | cut -d' ' -f1)
now=$(date +%s)
if [ -f "$STATE" ]; then
  read -r old_sig old_time < "$STATE"
  if [ "$old_sig" = "$sig" ] && [ $(( now - old_time )) -lt 21600 ]; then exit 1; fi
fi
echo "$sig $now" > "$STATE"
send "ALERT:
$msg"
exit 1
