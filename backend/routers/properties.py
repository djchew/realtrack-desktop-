from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Property
from database.utils import serialize

router = APIRouter()


class PropertyCreate(BaseModel):
    name: str
    address: str
    city: str
    state: str
    zip: str
    property_type: str
    status: str = "active"
    purchase_price: Optional[float] = None
    current_value: Optional[float] = None
    purchase_date: Optional[date] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    year_built: Optional[int] = None
    notes: Optional[str] = None


class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    property_type: Optional[str] = None
    status: Optional[str] = None
    purchase_price: Optional[float] = None
    current_value: Optional[float] = None
    purchase_date: Optional[date] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    year_built: Optional[int] = None
    notes: Optional[str] = None


@router.get("/properties")
def get_properties(db: Session = Depends(get_db)):
    props = db.query(Property).order_by(Property.created_at.desc()).all()
    return [serialize(p) for p in props]


@router.get("/properties/{id}")
def get_property(id: str, db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return serialize(prop)


@router.post("/properties", status_code=201)
def create_property(body: PropertyCreate, db: Session = Depends(get_db)):
    prop = Property(**body.model_dump(exclude_none=True))
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return serialize(prop)


@router.put("/properties/{id}")
def update_property(id: str, body: PropertyUpdate, db: Session = Depends(get_db)):
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    prop = db.query(Property).filter(Property.id == id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    for key, val in data.items():
        setattr(prop, key, val)
    db.commit()
    db.refresh(prop)
    return serialize(prop)


@router.delete("/properties/{id}", status_code=204)
def delete_property(id: str, db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    db.delete(prop)
    db.commit()
