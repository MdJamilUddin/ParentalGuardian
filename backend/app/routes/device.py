import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth.deps import current_device
from ..models.db import get_db
from ..models.entities import BatteryReading, Device, LocationPoint, UsageRecord, utcnow
from ..models.schemas import PairIn, PairOut, SyncIn, SyncOut
from ..services import alerts, push
from ..services.pairing import redeem_pairing_code
from ..services.ratelimit import RateLimiter

pair_limit = RateLimiter(10, 600)
router = APIRouter(prefix="/device", tags=["device"])
log = logging.getLogger("app.device")


@router.post("/pair", response_model=PairOut, dependencies=[Depends(pair_limit)])
def pair(body: PairIn, db: Session = Depends(get_db)):
    result = redeem_pairing_code(db, body.code, body.device_name)
    if not result:
        raise HTTPException(400, "Invalid or expired pairing code")
    device, token = result
    return PairOut(device_id=device.id, device_token=token)


@router.post("/sync", response_model=SyncOut)
def sync(body: SyncIn, background: BackgroundTasks, device: Device = Depends(current_device),
         db: Session = Depends(get_db)):
    for p in body.locations:
        db.add(LocationPoint(device_id=device.id, lat=p.lat, lng=p.lng, accuracy_m=p.accuracy_m,
                             recorded_at=p.recorded_at.replace(tzinfo=None)))
    for b in body.battery:
        db.add(BatteryReading(device_id=device.id, level=b.level, charging=b.charging,
                              recorded_at=b.recorded_at.replace(tzinfo=None)))
    for u in body.usage:  # daily totals: last value wins
        row = db.query(UsageRecord).filter_by(device_id=device.id, package=u.package, day=u.day).first()
        if row:
            row.seconds, row.app_label = u.seconds, (u.app_label or row.app_label)
        else:
            db.add(UsageRecord(device_id=device.id, package=u.package, app_label=u.app_label,
                               day=u.day, seconds=u.seconds))

    low_battery_message = None
    if body.battery:
        newest = max(body.battery, key=lambda b: alerts.to_naive_utc(b.recorded_at))
        low_battery_message = alerts.battery_alert(
            device, newest.level, newest.charging, alerts.to_naive_utc(newest.recorded_at))
    parent = device.child.parent
    notify, parent_id, child_name, child_id = parent.notify_low_battery, parent.id, device.child.name, device.child_id

    db.commit()
    if low_battery_message and notify:
        background.add_task(push.push_to_parent, parent_id, f"{child_name}: battery is low",
                            low_battery_message, {"type": "low_battery", "child_id": child_id})
    log.info("sync device=%s locations=%d usage=%d battery=%d", device.id,
             len(body.locations), len(body.usage), len(body.battery))
    return SyncOut(accepted_locations=len(body.locations), accepted_usage=len(body.usage),
                   accepted_battery=len(body.battery), server_time=utcnow())
