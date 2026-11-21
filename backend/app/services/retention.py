from datetime import timedelta

from sqlalchemy.orm import Session

from ..config.settings import settings
from ..models.entities import BatteryReading, LocationPoint, PairingCode, UsageRecord, utcnow


def purge_old_data(db: Session) -> None:
    cutoff = utcnow() - timedelta(days=settings.RETENTION_DAYS)
    db.query(LocationPoint).filter(LocationPoint.recorded_at < cutoff).delete()
    db.query(BatteryReading).filter(BatteryReading.recorded_at < cutoff).delete()
    db.query(UsageRecord).filter(UsageRecord.day < cutoff.strftime("%Y-%m-%d")).delete()
    db.query(PairingCode).filter(PairingCode.expires_at < cutoff).delete()
    db.commit()
