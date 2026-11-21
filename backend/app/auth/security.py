import hashlib
import hmac
import os
import secrets
from datetime import timedelta

import jwt

from ..config.settings import settings
from ..models.entities import utcnow

_ITER = 200_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITER)
    return f"{salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, dk_hex = stored.split("$")
    except ValueError:
        return False
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), _ITER)
    return hmac.compare_digest(dk.hex(), dk_hex)


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def new_device_token() -> str:
    return secrets.token_urlsafe(32)


def create_access_token(parent_id: int) -> str:
    exp = utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES)
    return jwt.encode({"sub": str(parent_id), "exp": exp}, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
