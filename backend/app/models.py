from datetime import datetime, timezone

from sqlalchemy import DateTime, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class InfrastructureDevice(Base):
    __tablename__ = "infrastructure_devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    location: Mapped[str] = mapped_column(String(100), default="Venue")
    address: Mapped[str] = mapped_column(String(100), default="")
    status: Mapped[str] = mapped_column(String(20), default="up", index=True)
    last_check: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(180))
    severity: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(30), default="new", index=True)
    source: Mapped[str] = mapped_column(String(120))
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    history: Mapped[list] = mapped_column(JSON, default=list)


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(180))
    category: Mapped[str] = mapped_column(String(60), default="Infrastructure")
    impact: Mapped[str] = mapped_column(String(30), default="department")
    urgency: Mapped[str] = mapped_column(String(30), default="normal")
    priority: Mapped[str] = mapped_column(String(4), default="P3", index=True)
    status: Mapped[str] = mapped_column(String(30), default="new", index=True)
    business_impact: Mapped[str] = mapped_column(Text, default="")
    owner: Mapped[str] = mapped_column(String(100), default="Night Operations")
    resolution: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    timeline: Mapped[list] = mapped_column(JSON, default=list)


class VendorTicket(Base):
    __tablename__ = "vendor_tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(100))
    circuit_id: Mapped[str] = mapped_column(String(100))
    ticket_number: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(40), default="open", index=True)
    contact: Mapped[str] = mapped_column(String(180), default="")
    sla_target: Mapped[str] = mapped_column(String(100), default="")
    last_update: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    history: Mapped[list] = mapped_column(JSON, default=list)


class Handoff(Base):
    __tablename__ = "handoffs"

    id: Mapped[int] = mapped_column(primary_key=True)
    operator: Mapped[str] = mapped_column(String(100))
    shift: Mapped[str] = mapped_column(String(60), default="Overnight")
    report: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
