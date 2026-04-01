from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session, joinedload

from database.connection import get_db
from database.models import Event
from database.utils import serialize

router = APIRouter()


class EventCreate(BaseModel):
    property_id: Optional[str] = None
    title: str
    category: str
    due_date: date
    status: str = "pending"
    notes: Optional[str] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None


@router.get("/events")
def get_events(upcoming: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Event).options(joinedload(Event.property))
    if upcoming:
        query = (
            query
            .filter(Event.due_date >= date.today(), Event.status == "pending")
            .order_by(Event.due_date)
            .limit(upcoming)
        )
    else:
        query = query.order_by(Event.due_date)

    events = query.all()
    result = []
    for e in events:
        d = serialize(e)
        d["properties"] = (
            {"name": e.property.name, "address": e.property.address}
            if e.property else None
        )
        result.append(d)
    return result


@router.post("/events", status_code=201)
def create_event(body: EventCreate, db: Session = Depends(get_db)):
    event = Event(**body.model_dump(exclude_none=True))
    db.add(event)
    db.commit()
    db.refresh(event)
    return serialize(event)


@router.put("/events/{id}")
def update_event(id: str, body: EventUpdate, db: Session = Depends(get_db)):
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    event = db.query(Event).filter(Event.id == id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    for key, val in data.items():
        setattr(event, key, val)
    db.commit()
    db.refresh(event)
    return serialize(event)


@router.delete("/events/{id}", status_code=204)
def delete_event(id: str, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(event)
    db.commit()
