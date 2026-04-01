from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Tenant
from database.utils import serialize

router = APIRouter()


class TenantCreate(BaseModel):
    property_id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    unit: Optional[str] = None
    rent_amount: float
    lease_start: date
    lease_end: Optional[date] = None
    status: str = "active"
    security_deposit: Optional[float] = None
    notes: Optional[str] = None


class TenantUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    unit: Optional[str] = None
    rent_amount: Optional[float] = None
    lease_start: Optional[date] = None
    lease_end: Optional[date] = None
    status: Optional[str] = None
    security_deposit: Optional[float] = None
    notes: Optional[str] = None


@router.get("/properties/{property_id}/tenants")
def get_tenants(property_id: str, db: Session = Depends(get_db)):
    tenants = (
        db.query(Tenant)
        .filter(Tenant.property_id == property_id)
        .order_by(Tenant.status)
        .all()
    )
    return [serialize(t) for t in tenants]


@router.post("/tenants", status_code=201)
def create_tenant(body: TenantCreate, db: Session = Depends(get_db)):
    tenant = Tenant(**body.model_dump(exclude_none=True))
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return serialize(tenant)


@router.put("/tenants/{id}")
def update_tenant(id: str, body: TenantUpdate, db: Session = Depends(get_db)):
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    tenant = db.query(Tenant).filter(Tenant.id == id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    for key, val in data.items():
        setattr(tenant, key, val)
    db.commit()
    db.refresh(tenant)
    return serialize(tenant)


@router.delete("/tenants/{id}", status_code=204)
def delete_tenant(id: str, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    db.delete(tenant)
    db.commit()
