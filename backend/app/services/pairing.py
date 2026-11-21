import secrets
from datetime import timedelta

from sqlalchemy.orm import Session

from ..auth.security import new_device_token, sha256
from ..config.settings import settings
from ..models.entities import Child, Device, PairingCode, utcnow


def create_pairing_code(db: Session, child: Child):
    code = f"{secrets.randbelow(1_000_000):06d}"
    expires = utcnow() + timedelta(minutes=settings.PAIRING_CODE_MINUTES)
    db.add(PairingCode(child_id=child.id, code_hash=sha256(code), expires_at=expires))
    db.commit()
    return code, expires


def redeem_pairing_code(db: Session, code: str, device_name: str):
    pc = db.query(PairingCode).filter(PairingCode.code_hash == sha256(code)).first()
    if not pc or pc.used or pc.expires_at < utcnow():
        return None
    pc.used = True
    token = new_device_token()
    device = Device(child_id=pc.child_id, name=device_name, token_hash=sha256(token))
    db.add(device)
    db.commit()
    db.refresh(device)
    return device, token
