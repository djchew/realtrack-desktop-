from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session, joinedload

from database.connection import get_db
from database.models import IncomeRecord
from database.utils import serialize

router = APIRouter()


class IncomeCreate(BaseModel):
    property_id: str
    tenant_id: Optional[str] = None
    category: str
    amount: float
    date: date
    description: Optional[str] = None


@router.get("/properties/{property_id}/income")
def get_income(property_id: str, month: Optional[str] = None, db: Session = Depends(get_db)):
    query = (
        db.query(IncomeRecord)
        .options(joinedload(IncomeRecord.tenant))
        .filter(IncomeRecord.property_id == property_id)
    )
    if month:
        query = query.filter(IncomeRecord.month == month)
    records = query.order_by(IncomeRecord.date.desc()).all()

    result = []
    for r in records:
        d = serialize(r)
        d["tenants"] = (
            {"first_name": r.tenant.first_name, "last_name": r.tenant.last_name}
            if r.tenant else None
        )
        result.append(d)
    return result


@router.post("/income", status_code=201)
def create_income(body: IncomeCreate, db: Session = Depends(get_db)):
    data = body.model_dump(exclude_none=True)
    data["month"] = str(data["date"])[:7]  # "YYYY-MM"
    record = IncomeRecord(**data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return serialize(record)


@router.delete("/income/{id}", status_code=204)
def delete_income(id: str, db: Session = Depends(get_db)):
    record = db.query(IncomeRecord).filter(IncomeRecord.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Income record not found")
    db.delete(record)
    db.commit()
