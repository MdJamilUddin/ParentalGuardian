import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..auth.security import create_access_token, hash_password, verify_password
from ..models.db import get_db
from ..models.entities import Parent
from ..models.schemas import LoginIn, RegisterIn, TokenOut
from ..services.ratelimit import RateLimiter

login_limit = RateLimiter(10, 300)
register_limit = RateLimiter(10, 3600)

router = APIRouter(prefix="/auth", tags=["auth"])
log = logging.getLogger("app.auth")


@router.post("/register", response_model=TokenOut, status_code=201, dependencies=[Depends(register_limit)])
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.query(Parent).filter(Parent.email == email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    parent = Parent(email=email, name=body.name, password_hash=hash_password(body.password))
    db.add(parent)
    db.commit()
    return TokenOut(access_token=create_access_token(parent.id))


@router.post("/login", response_model=TokenOut, dependencies=[Depends(login_limit)])
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    parent = db.query(Parent).filter(Parent.email == body.email.lower()).first()
    if not parent or not verify_password(body.password, parent.password_hash):
        log.warning("login failed ip=%s", request.client.host if request.client else "?")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong email or password")
    return TokenOut(access_token=create_access_token(parent.id))
