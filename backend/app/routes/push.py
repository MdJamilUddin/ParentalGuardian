from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth.deps import current_parent
from ..models.db import get_db
from ..models.entities import Parent, PushToken, utcnow
from ..services import push
from ..services.ratelimit import RateLimiter

router = APIRouter(prefix="/me", tags=["notifications"])
test_limit = RateLimiter(5, 60)


class PushTokenIn(BaseModel):
    token: str = Field(min_length=20, max_length=512)
    platform: str = Field(default="android", max_length=20)


class TokenOnly(BaseModel):
    token: str = Field(min_length=20, max_length=512)


class PrefsIn(BaseModel):
    offline: bool
    low_battery: bool


class PrefsOut(PrefsIn):
    devices: int


@router.put("/push-token", status_code=204)
def register_token(body: PushTokenIn, parent: Parent = Depends(current_parent), db: Session = Depends(get_db)):
    row = db.query(PushToken).filter(PushToken.token == body.token).first()
    if row:  # same phone, different account: it now belongs to the logged-in parent
        row.parent_id, row.updated_at = parent.id, utcnow()
    else:
        db.add(PushToken(parent_id=parent.id, token=body.token, platform=body.platform))
    db.commit()


@router.post("/push-token/unregister", status_code=204)
def unregister_token(body: TokenOnly, parent: Parent = Depends(current_parent), db: Session = Depends(get_db)):
    db.query(PushToken).filter(PushToken.token == body.token, PushToken.parent_id == parent.id).delete()
    db.commit()


def _prefs(parent: Parent, db: Session) -> PrefsOut:
    n = db.query(PushToken).filter(PushToken.parent_id == parent.id).count()
    return PrefsOut(offline=parent.notify_offline, low_battery=parent.notify_low_battery, devices=n)


@router.get("/notifications", response_model=PrefsOut)
def get_prefs(parent: Parent = Depends(current_parent), db: Session = Depends(get_db)):
    return _prefs(parent, db)


@router.put("/notifications", response_model=PrefsOut)
def set_prefs(body: PrefsIn, parent: Parent = Depends(current_parent), db: Session = Depends(get_db)):
    parent.notify_offline, parent.notify_low_battery = body.offline, body.low_battery
    db.commit()
    return _prefs(parent, db)


@router.post("/push-test", dependencies=[Depends(test_limit)])
def send_test(parent: Parent = Depends(current_parent), db: Session = Depends(get_db)):
    registered = db.query(PushToken).filter(PushToken.parent_id == parent.id).count()
    sent = push.notify_parent(db, parent.id, "Test notification", "Notifications are working.", {"type": "test"})
    return {"sent": sent, "registered": registered, "configured": push.get_sender().configured}
