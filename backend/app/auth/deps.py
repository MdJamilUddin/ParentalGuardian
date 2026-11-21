from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..models.db import get_db
from ..models.entities import Device, Parent, utcnow
from .security import decode_access_token, sha256

bearer = HTTPBearer()


def current_parent(
    cred: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)
) -> Parent:
    pid = decode_access_token(cred.credentials)
    parent = db.get(Parent, pid) if pid else None
    if not parent:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    return parent


def current_device(
    cred: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)
) -> Device:
    device = db.query(Device).filter(Device.token_hash == sha256(cred.credentials)).first()
    if not device or device.revoked:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or revoked device")
    device.last_seen = utcnow()
    return device
