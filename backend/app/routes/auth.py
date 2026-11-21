from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth.security import create_access_token, hash_password, verify_password
from ..models.db import get_db
from ..models.entities import Parent
from ..models.schemas import LoginIn, RegisterIn, TokenOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.query(Parent).filter(Parent.email == email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    parent = Parent(email=email, name=body.name, password_hash=hash_password(body.password))
    db.add(parent)
    db.commit()
    return TokenOut(access_token=create_access_token(parent.id))


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    parent = db.query(Parent).filter(Parent.email == body.email.lower()).first()
    if not parent or not verify_password(body.password, parent.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong email or password")
    return TokenOut(access_token=create_access_token(parent.id))
