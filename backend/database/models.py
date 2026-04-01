import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Float, Integer, Boolean, Date, DateTime, ForeignKey,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


class Property(Base):
    __tablename__ = "properties"

    id              = Column(String, primary_key=True, default=_uuid)
    name            = Column(String, nullable=False)
    address         = Column(String, nullable=False)
    city            = Column(String, nullable=False)
    state           = Column(String, nullable=False)
    zip             = Column(String, nullable=False)
    property_type   = Column(String, nullable=False)
    status          = Column(String, nullable=False, default="active")
    purchase_price  = Column(Float)
    current_value   = Column(Float)
    purchase_date   = Column(Date)
    bedrooms        = Column(Integer)
    bathrooms       = Column(Float)
    square_feet     = Column(Integer)
    year_built      = Column(Integer)
    notes           = Column(Text)
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    mortgages            = relationship("Mortgage",            back_populates="property", cascade="all, delete-orphan")
    tenants              = relationship("Tenant",              back_populates="property", cascade="all, delete-orphan")
    income_records       = relationship("IncomeRecord",        back_populates="property", cascade="all, delete-orphan")
    expense_records      = relationship("ExpenseRecord",       back_populates="property", cascade="all, delete-orphan")
    events               = relationship("Event",               back_populates="property", cascade="all, delete-orphan")
    maintenance_requests = relationship("MaintenanceRequest",  back_populates="property", cascade="all, delete-orphan")


class Mortgage(Base):
    __tablename__ = "mortgages"

    id               = Column(String, primary_key=True, default=_uuid)
    property_id      = Column(String, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    lender           = Column(String, nullable=False)
    loan_type        = Column(String, nullable=False, default="conventional")
    original_amount  = Column(Float, nullable=False)
    current_balance  = Column(Float, nullable=False)
    interest_rate    = Column(Float, nullable=False)
    monthly_payment  = Column(Float, nullable=False)
    start_date       = Column(Date, nullable=False)
    term_months      = Column(Integer, nullable=False)
    is_primary       = Column(Boolean, nullable=False, default=True)
    notes            = Column(Text)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property = relationship("Property", back_populates="mortgages")


class Tenant(Base):
    __tablename__ = "tenants"

    id               = Column(String, primary_key=True, default=_uuid)
    property_id      = Column(String, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    first_name       = Column(String, nullable=False)
    last_name        = Column(String, nullable=False)
    email            = Column(String)
    phone            = Column(String)
    unit             = Column(String)
    rent_amount      = Column(Float, nullable=False)
    lease_start      = Column(Date, nullable=False)
    lease_end        = Column(Date)
    status           = Column(String, nullable=False, default="active")
    security_deposit = Column(Float)
    notes            = Column(Text)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property      = relationship("Property", back_populates="tenants")
    income_records = relationship("IncomeRecord", back_populates="tenant")


class IncomeRecord(Base):
    __tablename__ = "income_records"

    id          = Column(String, primary_key=True, default=_uuid)
    property_id = Column(String, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    tenant_id   = Column(String, ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True)
    category    = Column(String, nullable=False)
    amount      = Column(Float, nullable=False)
    date        = Column(Date, nullable=False)
    month       = Column(String, nullable=False)  # "YYYY-MM"
    description = Column(Text)
    created_at  = Column(DateTime, default=datetime.utcnow)

    property = relationship("Property", back_populates="income_records")
    tenant   = relationship("Tenant", back_populates="income_records")


class ExpenseRecord(Base):
    __tablename__ = "expense_records"

    id           = Column(String, primary_key=True, default=_uuid)
    property_id  = Column(String, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    category     = Column(String, nullable=False)
    amount       = Column(Float, nullable=False)
    date         = Column(Date, nullable=False)
    month        = Column(String, nullable=False)  # "YYYY-MM"
    vendor       = Column(String)
    description  = Column(Text)
    is_recurring = Column(Boolean, nullable=False, default=False)
    created_at   = Column(DateTime, default=datetime.utcnow)

    property = relationship("Property", back_populates="expense_records")


class WatchlistItem(Base):
    __tablename__ = "watchlist"

    id             = Column(String, primary_key=True, default=_uuid)
    listing_url    = Column(Text)
    address        = Column(String, nullable=False)
    suburb         = Column(String)
    state          = Column(String)
    asking_price   = Column(Float)
    bedrooms       = Column(Integer)
    bathrooms      = Column(Float)
    parking        = Column(Integer)
    land_size      = Column(Integer)
    property_type  = Column(String)
    status         = Column(String, nullable=False, default="watching")
    notes          = Column(Text)
    og_title       = Column(Text)
    og_image       = Column(Text)
    og_description = Column(Text)
    created_at     = Column(DateTime, default=datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"

    id             = Column(String, primary_key=True, default=_uuid)
    property_id    = Column(String, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    title          = Column(String, nullable=False)
    category       = Column(String, nullable=False)
    priority       = Column(String, nullable=False, default="medium")
    status         = Column(String, nullable=False, default="open")
    reported_date  = Column(Date)
    completed_date = Column(Date)
    cost           = Column(Float)
    vendor         = Column(String)
    notes          = Column(Text)
    created_at     = Column(DateTime, default=datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property = relationship("Property", back_populates="maintenance_requests")


class Event(Base):
    __tablename__ = "events"

    id          = Column(String, primary_key=True, default=_uuid)
    property_id = Column(String, ForeignKey("properties.id", ondelete="CASCADE"), nullable=True)
    title       = Column(String, nullable=False)
    category    = Column(String, nullable=False)
    due_date    = Column(Date, nullable=False)
    status      = Column(String, nullable=False, default="pending")
    notes       = Column(Text)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property = relationship("Property", back_populates="events")
