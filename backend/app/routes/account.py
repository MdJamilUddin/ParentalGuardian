from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth.deps import current_parent
from ..auth.security import verify_password
from ..models.db import get_db
from ..models.entities import Parent
from ..services import account
from ..services.ratelimit import RateLimiter

router = APIRouter(prefix="/me", tags=["account"])
delete_limit = RateLimiter(5, 600)


class DeleteIn(BaseModel):
    password: str


@router.post("/delete", status_code=204, dependencies=[Depends(delete_limit)])
def delete_me(body: DeleteIn, parent: Parent = Depends(current_parent), db: Session = Depends(get_db)):
    """Deletes the account and all its data. Requires the password so a stolen login token is not enough."""
    if not verify_password(body.password, parent.password_hash):
        raise HTTPException(403, "Wrong password")
    account.delete_account(db, parent)


@router.get("/export")
def export_me(parent: Parent = Depends(current_parent), db: Session = Depends(get_db)):
    return account.export_data(db, parent)
