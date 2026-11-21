#!/usr/bin/env bash
# Daily database backup, keeps 14 days. Cron example (02:30 every day):
#   30 2 * * * /path/to/ParentalGuardian/deployment/backup.sh
# Restore:  gunzip -c backups/guardian-YYYY-MM-DD.sql.gz | docker compose exec -T db psql -U guardian guardian
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p backups
docker compose exec -T db pg_dump -U guardian guardian | gzip > "backups/guardian-$(date +%F).sql.gz"
find backups -name 'guardian-*.sql.gz' -mtime +14 -delete
