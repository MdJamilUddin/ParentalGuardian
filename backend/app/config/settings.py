import os


class Settings:
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_JSON = os.getenv("LOG_JSON", "false").lower() in ("1", "true", "yes")
    SENTRY_DSN = os.getenv("SENTRY_DSN", "")
    AUTO_MIGRATE = os.getenv("AUTO_MIGRATE", "true").lower() in ("1", "true", "yes")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./guardian.db")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
    PAIRING_CODE_MINUTES = int(os.getenv("PAIRING_CODE_MINUTES", "10"))
    RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "30"))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")


settings = Settings()
