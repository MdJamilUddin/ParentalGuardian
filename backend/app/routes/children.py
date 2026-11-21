from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth.deps import current_parent
from ..models.db import get_db
from ..models.entities import BatteryReading, Child, Device, LocationPoint, Parent, UsageRecord, utcnow
from ..models.schemas import BatteryOut, ChildIn, ChildOut, LocationOut, PairingCodeOut, UsageOut
from ..services.pairing import create_pairing_code

router = APIRouter(tags=["children"])


def _own_child(db: Session, parent: Parent, child_id: int) -> Child:
    child = db.get(Child, child_id)
    if not child or child.parent_id != parent.id:
        raise HTTPException(404, "Child not found")
    return child


def _device_ids(child: Child) -> list[int]:
    return [d.id for d in child.devices if not d.revoked]


@router.post("/children", response_model=ChildOut, status_code=201)
def add_child(body: ChildIn, parent: Parent = Depends(current_parent), db: Session = Depends(get_db)):
    child = Child(parent_id=parent.id, name=body.name)
    db.add(child)
    db.commit()
    db.refresh(child)
    return child


@router.get("/children", response_model=list[ChildOut])
def list_children(parent: Parent = Depends(current_parent), db: Session = Depends(get_db)):
    return db.query(Child).filter(Child.parent_id == parent.id).all()


@router.post("/children/{child_id}/pairing-code", response_model=PairingCodeOut)
def pairing_code(child_id: int, parent: Parent = Depends(current_parent), db: Session = Depends(get_db)):
    code, expires = create_pairing_code(db, _own_child(db, parent, child_id))
    return PairingCodeOut(code=code, expires_at=expires)


@router.delete("/devices/{device_id}", status_code=204)
def revoke_device(device_id: int, parent: Parent = Depends(current_parent), db: Session = Depends(get_db)):
    device = db.get(Device, device_id)
    if not device or device.child.parent_id != parent.id:
        raise HTTPException(404, "Device not found")
    device.revoked = True
    db.commit()


@router.get("/children/{child_id}/location/latest", response_model=LocationOut | None)
def latest_location(child_id: int, parent: Parent = Depends(current_parent), db: Session = Depends(get_db)):
    ids = _device_ids(_own_child(db, parent, child_id))
    return (db.query(LocationPoint).filter(LocationPoint.device_id.in_(ids))
            .order_by(LocationPoint.recorded_at.desc()).first())


@router.get("/children/{child_id}/locations", response_model=list[LocationOut])
def location_history(child_id: int, hours: int = Query(24, ge=1, le=720),
                     parent: Parent = Depends(current_parent), db: Session = Depends(get_db)):
    ids = _device_ids(_own_child(db, parent, child_id))
    since = utcnow() - timedelta(hours=hours)
    return (db.query(LocationPoint)
            .filter(LocationPoint.device_id.in_(ids), LocationPoint.recorded_at >= since)
            .order_by(LocationPoint.recorded_at.desc()).limit(2000).all())


@router.get("/children/{child_id}/usage", response_model=list[UsageOut])
def usage(child_id: int, day: str | None = None,
          parent: Parent = Depends(current_parent), db: Session = Depends(get_db)):
    ids = _device_ids(_own_child(db, parent, child_id))
    day = day or utcnow().strftime("%Y-%m-%d")
    return (db.query(UsageRecord).filter(UsageRecord.device_id.in_(ids), UsageRecord.day == day)
            .order_by(UsageRecord.seconds.desc()).all())


@router.get("/children/{child_id}/battery", response_model=BatteryOut | None)
def battery(child_id: int, parent: Parent = Depends(current_parent), db: Session = Depends(get_db)):
    ids = _device_ids(_own_child(db, parent, child_id))
    return (db.query(BatteryReading).filter(BatteryReading.device_id.in_(ids))
            .order_by(BatteryReading.recorded_at.desc()).first())
