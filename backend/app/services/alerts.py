import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from ..config.settings import settings
from ..models.db import SessionLocal
from ..models.entities import Device, utcnow
from .push import notify_parent

log = logging.getLogger("app.alerts")


def to_naive_utc(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt


def _duration(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    return f"{h} h {m} min" if h else f"{m} min"


def battery_alert(device: Device, level: int, charging: bool, recorded_at: datetime) -> str | None:
    """Updates the device's alert state. Returns the message when a low-battery alert should be sent.

    One alert per low period: it re-arms once the phone charges or climbs back above the reset level."""
    if recorded_at < utcnow() - timedelta(minutes=30):
        return None  # an old queued reading, not news
    if charging or level >= settings.LOW_BATTERY_RESET_PERCENT:
        device.low_battery_alert_sent_at = None
        return None
    if level <= settings.LOW_BATTERY_PERCENT and device.low_battery_alert_sent_at is None:
        device.low_battery_alert_sent_at = utcnow()
        return f"Battery is at {level}% and not charging."
    return None


def check_stale_devices(db: Session, now: datetime | None = None) -> int:
    """Alerts parents about phones that stopped reporting. One alert per outage. Returns alerts sent."""
    now = now or utcnow()
    cutoff = now - timedelta(minutes=settings.STALE_AFTER_MINUTES)
    devices = (
        db.query(Device)
        .filter(Device.revoked.is_(False))
        .filter(or_(Device.last_seen < cutoff, and_(Device.last_seen.is_(None), Device.paired_at < cutoff)))
        .all()
    )
    sent = 0
    for d in devices:
        reference = d.last_seen or d.paired_at
        if d.stale_alert_sent_at and d.stale_alert_sent_at >= reference:
            continue  # already alerted for this outage
        d.stale_alert_sent_at = now
        parent = d.child.parent
        if not parent.notify_offline:
            continue
        minutes = int((now - reference).total_seconds() // 60)
        if d.last_seen is None:
            body = "The phone was paired but has not sent any data yet."
        else:
            body = f"No update for {_duration(minutes)}. It may be switched off, offline, or the app was stopped."
        notify_parent(db, parent.id, f"{d.child.name}: phone not reporting", body,
                      {"type": "offline", "child_id": d.child_id})
        sent += 1
    db.commit()
    return sent


def run_alert_check() -> int:
    with SessionLocal() as db:
        n = check_stale_devices(db)
    if n:
        log.info("sent %d offline alert(s)", n)
    return n
