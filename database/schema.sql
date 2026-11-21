-- ParentalGuardian schema (PostgreSQL 14+). Mirrors backend/app/models/entities.py.
-- All timestamps are UTC, stored without time zone.

CREATE TABLE parents (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    name          VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc')
);

CREATE TABLE children (
    id        SERIAL PRIMARY KEY,
    parent_id INTEGER NOT NULL REFERENCES parents(id) ON DELETE CASCADE,
    name      VARCHAR(100) NOT NULL
);
CREATE INDEX ix_children_parent ON children(parent_id);

CREATE TABLE devices (
    id         SERIAL PRIMARY KEY,
    child_id   INTEGER NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    name       VARCHAR(100) NOT NULL,
    token_hash CHAR(64) NOT NULL UNIQUE,          -- SHA-256 of the device token
    revoked    BOOLEAN NOT NULL DEFAULT FALSE,
    paired_at  TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
    last_seen  TIMESTAMP
);
CREATE INDEX ix_devices_child ON devices(child_id);

CREATE TABLE pairing_codes (
    id         SERIAL PRIMARY KEY,
    child_id   INTEGER NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    code_hash  CHAR(64) NOT NULL UNIQUE,          -- SHA-256 of the 6-digit code
    expires_at TIMESTAMP NOT NULL,
    used       BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX ix_pairing_child ON pairing_codes(child_id);

CREATE TABLE location_points (
    id          BIGSERIAL PRIMARY KEY,
    device_id   INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    lat         DOUBLE PRECISION NOT NULL CHECK (lat BETWEEN -90 AND 90),
    lng         DOUBLE PRECISION NOT NULL CHECK (lng BETWEEN -180 AND 180),
    accuracy_m  DOUBLE PRECISION,
    recorded_at TIMESTAMP NOT NULL
);
CREATE INDEX ix_location_device_time ON location_points(device_id, recorded_at DESC);

CREATE TABLE usage_records (
    id        BIGSERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    package   VARCHAR(255) NOT NULL,
    app_label VARCHAR(255),
    day       CHAR(10) NOT NULL,                  -- YYYY-MM-DD
    seconds   INTEGER NOT NULL CHECK (seconds BETWEEN 0 AND 86400),
    UNIQUE (device_id, package, day)
);
CREATE INDEX ix_usage_device_day ON usage_records(device_id, day);

CREATE TABLE battery_readings (
    id          BIGSERIAL PRIMARY KEY,
    device_id   INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    level       INTEGER NOT NULL CHECK (level BETWEEN 0 AND 100),
    charging    BOOLEAN NOT NULL DEFAULT FALSE,
    recorded_at TIMESTAMP NOT NULL
);
CREATE INDEX ix_battery_device_time ON battery_readings(device_id, recorded_at DESC);
