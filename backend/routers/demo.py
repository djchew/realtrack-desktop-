from fastapi import APIRouter, HTTPException, Depends
from datetime import date, timedelta
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import (
    Property, Mortgage, Tenant, IncomeRecord, ExpenseRecord,
    MaintenanceRequest, Event, WatchlistItem,
)

router = APIRouter()


@router.post("/demo/seed")
def seed_demo(db: Session = Depends(get_db)):
    """Populate the database with sample Australian property data."""
    try:
        today = date.today()

        p1 = Property(
            name="Bondi Beach Unit", address="12 Campbell Parade",
            city="Bondi Beach", state="NSW", zip="2026",
            property_type="condo", status="active",
            purchase_price=850000, current_value=1050000,
            purchase_date=date(2019, 3, 15),
            bedrooms=2, bathrooms=1, square_feet=720, year_built=2005,
        )
        p2 = Property(
            name="Fitzroy Terrace", address="44 Smith Street",
            city="Fitzroy", state="VIC", zip="3065",
            property_type="townhouse", status="active",
            purchase_price=720000, current_value=920000,
            purchase_date=date(2020, 8, 1),
            bedrooms=3, bathrooms=2, square_feet=1100, year_built=1998,
        )
        db.add_all([p1, p2])
        db.flush()  # get IDs before inserting children

        db.add_all([
            Mortgage(
                property_id=p1.id, lender="Commonwealth Bank",
                loan_type="conventional", original_amount=680000,
                current_balance=598000, interest_rate=0.0599,
                monthly_payment=3850, start_date=date(2019, 3, 15),
                term_months=360, is_primary=True,
            ),
            Mortgage(
                property_id=p2.id, lender="ANZ Bank",
                loan_type="conventional", original_amount=576000,
                current_balance=520000, interest_rate=0.0625,
                monthly_payment=3540, start_date=date(2020, 8, 1),
                term_months=360, is_primary=True,
            ),
        ])

        t1 = Tenant(
            property_id=p1.id, first_name="Sarah", last_name="Mitchell",
            email="sarah.mitchell@example.com", phone="0412 345 678",
            rent_amount=2800,
            lease_start=today - timedelta(days=180),
            lease_end=today + timedelta(days=185),
            status="active", security_deposit=5600,
        )
        t2 = Tenant(
            property_id=p2.id, first_name="James", last_name="Nguyen",
            email="james.nguyen@example.com", phone="0421 987 654",
            rent_amount=3200,
            lease_start=today - timedelta(days=90),
            lease_end=today + timedelta(days=275),
            status="active", security_deposit=6400,
        )
        db.add_all([t1, t2])

        # Income + expenses — last 3 months
        for i in range(3):
            m = today.replace(day=1) - timedelta(days=i * 30)
            month = str(m)[:7]
            d1 = m.replace(day=1)
            d5 = m.replace(day=5)
            db.add_all([
                IncomeRecord(property_id=p1.id, category="rent", amount=2800,  date=d1, month=month, description="Monthly rent"),
                IncomeRecord(property_id=p2.id, category="rent", amount=3200,  date=d1, month=month, description="Monthly rent"),
                ExpenseRecord(property_id=p1.id, category="insurance",    amount=180, date=d5, month=month, description="Landlord insurance",  is_recurring=True),
                ExpenseRecord(property_id=p2.id, category="property_tax", amount=420, date=d5, month=month, description="Council rates",        is_recurring=True),
            ])

        db.add_all([
            MaintenanceRequest(
                property_id=p1.id, title="Hot water system replacement",
                category="plumbing", priority="high", status="completed",
                reported_date=today - timedelta(days=30),
                completed_date=today - timedelta(days=20),
                cost=1850, vendor="Sydney Hot Water Pros",
                notes="Old unit failed, replaced with new 250L system.",
            ),
            MaintenanceRequest(
                property_id=p2.id, title="Roof gutter cleaning",
                category="landscaping", priority="medium", status="open",
                reported_date=today - timedelta(days=5),
            ),
            Event(
                property_id=p1.id, title="Lease renewal — Sarah Mitchell",
                category="lease_renewal",
                due_date=today + timedelta(days=30), status="pending",
            ),
            Event(
                property_id=p2.id, title="Annual landlord insurance renewal",
                category="insurance_renewal",
                due_date=today + timedelta(days=45), status="pending",
            ),
        ])

        db.commit()
        return {"ok": True, "properties_created": 2}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/demo/clear")
def clear_demo(db: Session = Depends(get_db)):
    """Remove all data (useful for resetting the demo)."""
    try:
        # Delete in FK-safe order
        db.query(Event).delete(synchronize_session=False)
        db.query(MaintenanceRequest).delete(synchronize_session=False)
        db.query(IncomeRecord).delete(synchronize_session=False)
        db.query(ExpenseRecord).delete(synchronize_session=False)
        db.query(Tenant).delete(synchronize_session=False)
        db.query(Mortgage).delete(synchronize_session=False)
        db.query(Property).delete(synchronize_session=False)
        db.query(WatchlistItem).delete(synchronize_session=False)
        db.commit()
        return {"ok": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
