import csv
import io
from collections import defaultdict
from datetime import date, timedelta
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from database.connection import get_db
from database.models import Property, Mortgage, Tenant, IncomeRecord, ExpenseRecord, Event
from database.utils import serialize

router = APIRouter()


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    # Portfolio summary (replaces v_portfolio_summary view)
    active_props = db.query(Property).filter(Property.status == "active").all()
    prop_ids = [p.id for p in active_props]

    portfolio_value = sum(p.current_value or 0 for p in active_props)
    mortgages = (
        db.query(Mortgage).filter(Mortgage.property_id.in_(prop_ids)).all()
        if prop_ids else []
    )
    total_debt = sum(m.current_balance for m in mortgages)
    total_monthly_mortgage = sum(m.monthly_payment for m in mortgages)

    # Current month income/expenses
    current_month = str(date.today())[:7]
    monthly_income = sum(
        r.amount for r in
        db.query(IncomeRecord).filter(IncomeRecord.month == current_month).all()
    )
    monthly_expenses = sum(
        r.amount for r in
        db.query(ExpenseRecord).filter(ExpenseRecord.month == current_month).all()
    )

    # Upcoming events (next 5 pending)
    upcoming = (
        db.query(Event)
        .options(joinedload(Event.property))
        .filter(Event.status == "pending", Event.due_date >= date.today())
        .order_by(Event.due_date)
        .limit(5)
        .all()
    )

    # Leases expiring within 60 days
    in_60 = date.today() + timedelta(days=60)
    expiring = (
        db.query(Tenant)
        .options(joinedload(Tenant.property))
        .filter(
            Tenant.status == "active",
            Tenant.lease_end >= date.today(),
            Tenant.lease_end <= in_60,
        )
        .order_by(Tenant.lease_end)
        .all()
    )

    return {
        "portfolio_value":        portfolio_value,
        "total_equity":           portfolio_value - total_debt,
        "total_debt":             total_debt,
        "total_monthly_mortgage": total_monthly_mortgage,
        "active_properties":      len(active_props),
        "current_month":          current_month,
        "monthly_income":         monthly_income,
        "monthly_expenses":       monthly_expenses,
        "monthly_cash_flow":      monthly_income - monthly_expenses,
        "upcoming_events": [
            {
                "id":         e.id,
                "title":      e.title,
                "due_date":   e.due_date.isoformat() if e.due_date else None,
                "category":   e.category,
                "properties": {"name": e.property.name} if e.property else None,
            }
            for e in upcoming
        ],
        "expiring_leases": [
            {
                "id":          t.id,
                "first_name":  t.first_name,
                "last_name":   t.last_name,
                "lease_end":   t.lease_end.isoformat() if t.lease_end else None,
                "rent_amount": t.rent_amount,
                "unit":        t.unit,
                "properties":  {"id": t.property.id, "name": t.property.name} if t.property else None,
            }
            for t in expiring
        ],
    }


@router.get("/summary/cash-flow")
def get_cash_flow(db: Session = Depends(get_db)):
    try:
        income_rows  = db.query(IncomeRecord).all()
        expense_rows = db.query(ExpenseRecord).all()
        props        = {p.id: p for p in db.query(Property).all()}

        # Aggregate by (property_id, month)
        monthly: dict = defaultdict(lambda: {"total_income": 0.0, "total_expenses": 0.0})
        for r in income_rows:
            monthly[(r.property_id, r.month)]["total_income"] += r.amount
        for r in expense_rows:
            monthly[(r.property_id, r.month)]["total_expenses"] += r.amount

        result = []
        for (prop_id, month), totals in monthly.items():
            if month and prop_id in props:
                p = props[prop_id]
                result.append({
                    "property_id":    prop_id,
                    "property_name":  p.name,
                    "address":        p.address,
                    "month":          month,
                    "total_income":   totals["total_income"],
                    "total_expenses": totals["total_expenses"],
                    "cash_flow":      totals["total_income"] - totals["total_expenses"],
                })

        result.sort(key=lambda x: x["month"], reverse=True)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/tax-export")
def get_tax_export(fy: int, db: Session = Depends(get_db)):
    """
    Download income + expenses for an Australian financial year as CSV.
    FY ending 30 June of `fy`, e.g. fy=2025 covers 2024-07-01 to 2025-06-30.
    """
    start = date(fy - 1, 7, 1)
    end   = date(fy, 6, 30)

    try:
        income_rows = (
            db.query(IncomeRecord)
            .options(joinedload(IncomeRecord.property))
            .filter(IncomeRecord.date >= start, IncomeRecord.date <= end)
            .order_by(IncomeRecord.date)
            .all()
        )
        expense_rows = (
            db.query(ExpenseRecord)
            .options(joinedload(ExpenseRecord.property))
            .filter(ExpenseRecord.date >= start, ExpenseRecord.date <= end)
            .order_by(ExpenseRecord.date)
            .all()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Type", "Date", "Property", "Category", "Amount (AUD)", "Description", "Vendor"])
    for r in income_rows:
        writer.writerow([
            "Income",
            r.date.isoformat() if r.date else "",
            r.property.name if r.property else "",
            r.category, r.amount, r.description or "", "",
        ])
    for r in expense_rows:
        writer.writerow([
            "Expense",
            r.date.isoformat() if r.date else "",
            r.property.name if r.property else "",
            r.category, r.amount, r.description or "", r.vendor or "",
        ])

    buf.seek(0)
    filename = f"tax_summary_FY{fy}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/summary/analytics")
def get_analytics(db: Session = Depends(get_db)):
    try:
        mortgages = db.query(Mortgage).all()
        tenants   = db.query(Tenant).all()
        return {
            "mortgages": [serialize(m) for m in mortgages],
            "tenants":   [serialize(t) for t in tenants],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
