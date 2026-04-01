from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import ExpenseRecord
from database.utils import serialize

router = APIRouter()


class ExpenseCreate(BaseModel):
    property_id: str
    category: str
    amount: float
    date: date
    vendor: Optional[str] = None
    description: Optional[str] = None
    is_recurring: bool = False


@router.get("/properties/{property_id}/expenses")
def get_expenses(property_id: str, month: Optional[str] = None, db: Session = Depends(get_db)):
    query = (
        db.query(ExpenseRecord)
        .filter(ExpenseRecord.property_id == property_id)
    )
    if month:
        query = query.filter(ExpenseRecord.month == month)
    records = query.order_by(ExpenseRecord.date.desc()).all()
    return [serialize(r) for r in records]


@router.post("/expenses", status_code=201)
def create_expense(body: ExpenseCreate, db: Session = Depends(get_db)):
    data = body.model_dump(exclude_none=True)
    data["month"] = str(data["date"])[:7]  # "YYYY-MM"
    record = ExpenseRecord(**data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return serialize(record)


@router.delete("/expenses/{id}", status_code=204)
def delete_expense(id: str, db: Session = Depends(get_db)):
    record = db.query(ExpenseRecord).filter(ExpenseRecord.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Expense record not found")
    db.delete(record)
    db.commit()
