-- Optional: run daily from cron (the backend also purges on startup). 30-day retention.
DELETE FROM location_points WHERE recorded_at < (now() AT TIME ZONE 'utc') - INTERVAL '30 days';
DELETE FROM battery_readings WHERE recorded_at < (now() AT TIME ZONE 'utc') - INTERVAL '30 days';
DELETE FROM usage_records   WHERE day < to_char((now() AT TIME ZONE 'utc') - INTERVAL '30 days', 'YYYY-MM-DD');
DELETE FROM pairing_codes   WHERE expires_at < (now() AT TIME ZONE 'utc') - INTERVAL '30 days';
