from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session, joinedload

from database.connection import get_db
from database.models import MaintenanceRequest
from database.utils import serialize

router = APIRouter()


class MaintenanceIn(BaseModel):
    property_id: str
    title: str
    category: str
    priority: str = "medium"
    status: str = "open"
    reported_date: Optional[str] = None
    completed_date: Optional[str] = None
    cost: Optional[float] = None
    vendor: Optional[str] = None
    notes: Optional[str] = None


@router.get("/maintenance")
def list_maintenance(
    property_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = (
        db.query(MaintenanceRequest)
        .options(joinedload(MaintenanceRequest.property))
        .order_by(MaintenanceRequest.reported_date.desc())
    )
    if property_id:
        query = query.filter(MaintenanceRequest.property_id == property_id)
    if status:
        query = query.filter(MaintenanceRequest.status == status)

    requests = query.all()
    result = []
    for r in requests:
        d = serialize(r)
        d["properties"] = {"name": r.property.name} if r.property else None
        result.append(d)
    return result


@router.post("/maintenance", status_code=201)
def create_maintenance(data: MaintenanceIn, db: Session = Depends(get_db)):
    req = MaintenanceRequest(**data.model_dump(exclude_none=True))
    db.add(req)
    db.commit()
    db.refresh(req)
    return serialize(req)


@router.put("/maintenance/{req_id}")
def update_maintenance(req_id: str, data: MaintenanceIn, db: Session = Depends(get_db)):
    req = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Not found")
    for key, val in data.model_dump(exclude_none=True).items():
        setattr(req, key, val)
    db.commit()
    db.refresh(req)
    return serialize(req)


@router.delete("/maintenance/{req_id}", status_code=204)
def delete_maintenance(req_id: str, db: Session = Depends(get_db)):
    req = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(req)
    db.commit()
