from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth.deps import current_parent
from ..models.db import get_db
from ..models.entities import LocationPoint, Parent, Place, utcnow
from ..services.places import distance_m
from .children import _device_ids, _own_child

router = APIRouter(tags=["places"])
MAX_PLACES = 10


class PlaceIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    radius_m: int = Field(default=150, ge=50, le=2000)


class PlaceOut(BaseModel):
    id: int
    name: str
    lat: float
    lng: float
    radius_m: int
    inside: bool | None
    model_config = {"from_attributes": True}


@router.get("/children/{child_id}/places", response_model=list[PlaceOut])
def list_places(child_id: int, parent: Parent = Depends(current_parent), db: Session = Depends(get_db)):
    return sorted(_own_child(db, parent, child_id).places, key=lambda p: p.id)


@router.post("/children/{child_id}/places", response_model=PlaceOut, status_code=201)
def add_place(child_id: int, body: PlaceIn, parent: Parent = Depends(current_parent), db: Session = Depends(get_db)):
    child = _own_child(db, parent, child_id)
    if len(child.places) >= MAX_PLACES:
        raise HTTPException(400, f"At most {MAX_PLACES} places per child")
    place = Place(child_id=child.id, name=body.name.strip(), lat=body.lat, lng=body.lng, radius_m=body.radius_m)
    ids = _device_ids(child)
    latest = (db.query(LocationPoint).filter(LocationPoint.device_id.in_(ids))
              .order_by(LocationPoint.recorded_at.desc()).first()) if ids else None
    if latest and (utcnow() - latest.recorded_at).total_seconds() < 6 * 3600:  # know the state from the start
        place.inside = distance_m(latest.lat, latest.lng, place.lat, place.lng) <= place.radius_m
    db.add(place)
    db.commit()
    db.refresh(place)
    return place


@router.delete("/places/{place_id}", status_code=204)
def delete_place(place_id: int, parent: Parent = Depends(current_parent), db: Session = Depends(get_db)):
    place = db.get(Place, place_id)
    if not place or place.child.parent_id != parent.id:
        raise HTTPException(404, "Place not found")
    db.delete(place)
    db.commit()
