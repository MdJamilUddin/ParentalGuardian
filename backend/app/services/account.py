from sqlalchemy.orm import Session

from ..models.entities import (BatteryReading, LocationPoint, PairingCode, Parent, PushToken, UsageRecord)

EXPORT_LIMIT = 20000  # rows per kind


def delete_account(db: Session, parent: Parent) -> None:
    """Permanently removes the parent, their children, phones, places, tokens and all collected data.
    Done explicitly so it also works on SQLite, which does not enforce ON DELETE CASCADE by default."""
    child_ids = [c.id for c in parent.children]
    device_ids = [d.id for c in parent.children for d in c.devices]
    if device_ids:
        for model in (LocationPoint, UsageRecord, BatteryReading):
            db.query(model).filter(model.device_id.in_(device_ids)).delete(synchronize_session=False)
    if child_ids:
        db.query(PairingCode).filter(PairingCode.child_id.in_(child_ids)).delete(synchronize_session=False)
    db.query(PushToken).filter(PushToken.parent_id == parent.id).delete(synchronize_session=False)
    db.delete(parent)  # the ORM cascades to children, devices and places
    db.commit()


def export_data(db: Session, parent: Parent) -> dict:
    """Everything stored about this parent (data portability)."""
    children = []
    for c in parent.children:
        ids = [d.id for d in c.devices]

        def rows(model, order):
            if not ids:
                return []
            return db.query(model).filter(model.device_id.in_(ids)).order_by(order.desc()).limit(EXPORT_LIMIT).all()

        children.append({
            "id": c.id,
            "name": c.name,
            "devices": [{"id": d.id, "name": d.name, "paired_at": d.paired_at, "last_seen": d.last_seen,
                         "revoked": d.revoked} for d in c.devices],
            "places": [{"name": p.name, "lat": p.lat, "lng": p.lng, "radius_m": p.radius_m} for p in c.places],
            "locations": [{"lat": r.lat, "lng": r.lng, "accuracy_m": r.accuracy_m, "recorded_at": r.recorded_at}
                          for r in rows(LocationPoint, LocationPoint.recorded_at)],
            "battery": [{"level": r.level, "charging": r.charging, "recorded_at": r.recorded_at}
                        for r in rows(BatteryReading, BatteryReading.recorded_at)],
            "app_usage": [{"package": r.package, "app_label": r.app_label, "day": r.day, "seconds": r.seconds}
                          for r in rows(UsageRecord, UsageRecord.day)],
        })
    return {
        "account": {"email": parent.email, "name": parent.name, "created_at": parent.created_at,
                    "terms_accepted_at": parent.terms_accepted_at, "terms_version": parent.terms_version},
        "children": children,
    }
