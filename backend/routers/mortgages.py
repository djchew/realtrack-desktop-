from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Mortgage
from database.utils import serialize

router = APIRouter()


class MortgageCreate(BaseModel):
    property_id: str
    lender: str
    loan_type: str = "conventional"
    original_amount: float
    current_balance: float
    interest_rate: float
    monthly_payment: float
    start_date: date
    term_months: int
    is_primary: bool = True
    notes: Optional[str] = None


class MortgageUpdate(BaseModel):
    lender: Optional[str] = None
    loan_type: Optional[str] = None
    current_balance: Optional[float] = None
    interest_rate: Optional[float] = None
    monthly_payment: Optional[float] = None
    is_primary: Optional[bool] = None
    notes: Optional[str] = None


@router.get("/properties/{property_id}/mortgages")
def get_mortgages(property_id: str, db: Session = Depends(get_db)):
    mortgages = (
        db.query(Mortgage)
        .filter(Mortgage.property_id == property_id)
        .order_by(Mortgage.is_primary.desc())
        .all()
    )
    return [serialize(m) for m in mortgages]


@router.post("/mortgages", status_code=201)
def create_mortgage(body: MortgageCreate, db: Session = Depends(get_db)):
    mortgage = Mortgage(**body.model_dump(exclude_none=True))
    db.add(mortgage)
    db.commit()
    db.refresh(mortgage)
    return serialize(mortgage)


@router.put("/mortgages/{id}")
def update_mortgage(id: str, body: MortgageUpdate, db: Session = Depends(get_db)):
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    mortgage = db.query(Mortgage).filter(Mortgage.id == id).first()
    if not mortgage:
        raise HTTPException(status_code=404, detail="Mortgage not found")
    for key, val in data.items():
        setattr(mortgage, key, val)
    db.commit()
    db.refresh(mortgage)
    return serialize(mortgage)


@router.delete("/mortgages/{id}", status_code=204)
def delete_mortgage(id: str, db: Session = Depends(get_db)):
    mortgage = db.query(Mortgage).filter(Mortgage.id == id).first()
    if not mortgage:
        raise HTTPException(status_code=404, detail="Mortgage not found")
    db.delete(mortgage)
    db.commit()
