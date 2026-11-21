from datetime import timedelta

from app.models.db import SessionLocal
from app.models.entities import BatteryReading, LocationPoint, UsageRecord, utcnow
from app.services.retention import purge_old_data


def test_old_data_is_purged_and_recent_data_kept(paired):
    p = paired()
    old = utcnow() - timedelta(days=40)
    new = utcnow() - timedelta(days=1)
    with SessionLocal() as db:
        db.add_all([
            LocationPoint(device_id=p.device_id, lat=1, lng=1, recorded_at=old),
            LocationPoint(device_id=p.device_id, lat=2, lng=2, recorded_at=new),
            BatteryReading(device_id=p.device_id, level=50, charging=False, recorded_at=old),
            BatteryReading(device_id=p.device_id, level=60, charging=False, recorded_at=new),
            UsageRecord(device_id=p.device_id, package="old", day=old.strftime("%Y-%m-%d"), seconds=10),
            UsageRecord(device_id=p.device_id, package="new", day=new.strftime("%Y-%m-%d"), seconds=10),
        ])
        db.commit()

        purge_old_data(db)

        assert [x.lat for x in db.query(LocationPoint).all()] == [2]
        assert [x.level for x in db.query(BatteryReading).all()] == [60]
        assert [x.package for x in db.query(UsageRecord).all()] == ["new"]
