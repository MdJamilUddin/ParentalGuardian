from datetime import datetime, timedelta, timezone


def iso(minutes_ago: int = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).isoformat()


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
