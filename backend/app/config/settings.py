import os


def normalize_database_url(url: str) -> str:
    """Hosting providers give postgres:// or postgresql:// URLs; SQLAlchemy needs the driver name too."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg2://" + url[len(prefix):]
    return url


class Settings:
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_JSON = os.getenv("LOG_JSON", "false").lower() in ("1", "true", "yes")
    SENTRY_DSN = os.getenv("SENTRY_DSN", "")
    # push notifications (Firebase Cloud Messaging). Empty = push disabled.
    FIREBASE_CREDENTIALS_JSON = os.getenv("FIREBASE_CREDENTIALS_JSON", "")  # service-account JSON, or its base64
    CRON_SECRET = os.getenv("CRON_SECRET", "")  # enables POST /internal/check-alerts for an external scheduler
    STALE_AFTER_MINUTES = int(os.getenv("STALE_AFTER_MINUTES", "120"))
    LOW_BATTERY_PERCENT = int(os.getenv("LOW_BATTERY_PERCENT", "15"))
    LOW_BATTERY_RESET_PERCENT = int(os.getenv("LOW_BATTERY_RESET_PERCENT", "30"))
    ALERT_CHECK_SECONDS = int(os.getenv("ALERT_CHECK_SECONDS", "300"))  # 0 = no in-process checker
    AUTO_MIGRATE = os.getenv("AUTO_MIGRATE", "true").lower() in ("1", "true", "yes")
    DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL", "sqlite:///./guardian.db"))
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
    PAIRING_CODE_MINUTES = int(os.getenv("PAIRING_CODE_MINUTES", "10"))
    RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "30"))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")


settings = Settings()
