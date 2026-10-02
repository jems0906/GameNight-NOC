from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from alembic import command
from alembic.config import Config
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.config import settings
from app.models import Alert, Handoff, Incident, InfrastructureDevice, VendorTicket
from app.monitoring.alert_engine import evaluate_devices
from app.seed import seed_database
from app.services import analyze_cli, build_handoff, build_handoff_trends, calculate_priority, stakeholder_summary


def new_incident_number() -> str:
    return f"INC-{datetime.now(timezone.utc):%y%m%d%H%M%S}-{uuid4().hex[:4].upper()}"


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    migration_config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(migration_config, "head")
    with SessionLocal() as session:
        seed_database(session)
    yield


app = FastAPI(title="GameNight NOC API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class IncidentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    category: str = "Infrastructure"
    impact: str = "department"
    urgency: str = "normal"
    business_impact: str = ""
    owner: str = "Night Operations"


class IncidentUpdate(BaseModel):
    status: str | None = None
    action: str | None = None
    resolution: str | None = None
    owner: str | None = None


class AlertUpdate(BaseModel):
    status: str


class VendorCreate(BaseModel):
    provider: str
    circuit_id: str
    ticket_number: str
    contact: str = ""
    sla_target: str = ""
    last_update: str = ""
    status: Literal["open", "awaiting vendor", "vendor investigating", "resolved"] = "open"


class VendorUpdate(BaseModel):
    status: Literal["open", "awaiting vendor", "vendor investigating", "resolved"] | None = None
    last_update: str | None = None


class HandoffCreate(BaseModel):
    operator: str = Field(min_length=1, max_length=100)
    shift: str = "Overnight"


class CiscoAnalyze(BaseModel):
    output: str = Field(min_length=1, max_length=30000)


class MonitoringEvaluate(BaseModel):
    alert_types: list[str] | None = None


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "gamenight-noc-api"}


@app.get("/api/infrastructure")
def infrastructure(session: Session = Depends(get_session)):
    devices = session.scalars(select(InfrastructureDevice).order_by(InfrastructureDevice.category, InfrastructureDevice.name)).all()
    return [{"id": item.id, "name": item.name, "category": item.category, "location": item.location, "address": item.address, "status": item.status, "last_check": item.last_check, "metrics": item.metrics} for item in devices]


@app.get("/api/alerts")
def alerts(status: str | None = None, session: Session = Depends(get_session)):
    query = select(Alert).order_by(Alert.created_at.desc())
    if status:
        query = query.where(Alert.status == status)
    return session.scalars(query).all()


@app.patch("/api/alerts/{alert_id}")
def update_alert(alert_id: int, payload: AlertUpdate, session: Session = Depends(get_session)):
    item = session.get(Alert, alert_id)
    if item is None:
        raise HTTPException(404, "Alert not found")
    if payload.status not in {"new", "acknowledged", "investigating", "resolved"}:
        raise HTTPException(422, "Unsupported alert status")
    item.history = [*item.history, {"at": datetime.now(timezone.utc).isoformat(), "status": payload.status}]
    item.status = payload.status
    item.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(item)
    return item


@app.post("/api/alerts/{alert_id}/incident", status_code=201)
def create_incident_from_alert(alert_id: int, session: Session = Depends(get_session)):
    alert = session.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(404, "Alert not found")
    urgency = "critical" if alert.severity == "critical" else "normal"
    item = Incident(number=new_incident_number(), title=alert.title, category="Infrastructure", impact="department", urgency=urgency, priority=calculate_priority("department", urgency), status="new", business_impact=f"Investigate operational impact associated with {alert.source}.", owner="Night Operations", timeline=[{"at": datetime.now(timezone.utc).isoformat(), "action": f"Created from {alert.severity} alert: {alert.detail}"}])
    session.add(item)
    alert.history = [*alert.history, {"at": datetime.now(timezone.utc).isoformat(), "status": "acknowledged", "action": f"Incident {item.number} created"}]
    alert.status = "acknowledged"
    alert.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(item)
    return item


@app.get("/api/incidents")
def incidents(status: str | None = None, session: Session = Depends(get_session)):
    query = select(Incident).order_by(Incident.created_at.desc())
    if status:
        query = query.where(Incident.status == status)
    return session.scalars(query).all()


@app.post("/api/incidents", status_code=201)
def create_incident(payload: IncidentCreate, session: Session = Depends(get_session)):
    valid_impacts = {"individual", "department", "multiple_departments", "venue_wide"}
    valid_urgencies = {"low", "normal", "high", "critical"}
    if payload.impact not in valid_impacts or payload.urgency not in valid_urgencies:
        raise HTTPException(422, "Unsupported impact or urgency")
    number = new_incident_number()
    item = Incident(number=number, title=payload.title, category=payload.category, impact=payload.impact, urgency=payload.urgency, priority=calculate_priority(payload.impact, payload.urgency), business_impact=payload.business_impact, owner=payload.owner, timeline=[{"at": datetime.now(timezone.utc).isoformat(), "action": "Incident created"}])
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@app.patch("/api/incidents/{incident_id}")
def update_incident(incident_id: int, payload: IncidentUpdate, session: Session = Depends(get_session)):
    item = session.get(Incident, incident_id)
    if item is None:
        raise HTTPException(404, "Incident not found")
    valid_statuses = {"new", "acknowledged", "investigating", "vendor engaged", "resolved", "handoff complete"}
    changes = payload.model_dump(exclude_none=True)
    status = changes.pop("status", None)
    action = changes.pop("action", None)
    resolution = changes.pop("resolution", None)
    if status and status not in valid_statuses:
        raise HTTPException(422, "Unsupported incident status")
    for key, value in changes.items():
        setattr(item, key, value)
    if status:
        item.status = status
    if resolution is not None:
        item.resolution = resolution
    if action or status or resolution:
        timeline_action = action or (f"Status updated to {status}" if status else "Resolution notes updated")
        item.timeline = [*item.timeline, {"at": datetime.now(timezone.utc).isoformat(), "action": timeline_action}]
    item.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(item)
    return item


@app.get("/api/vendor-tickets")
def vendor_tickets(session: Session = Depends(get_session)):
    return session.scalars(select(VendorTicket).order_by(VendorTicket.updated_at.desc())).all()


@app.post("/api/vendor-tickets", status_code=201)
def create_vendor_ticket(payload: VendorCreate, session: Session = Depends(get_session)):
    item = VendorTicket(**payload.model_dump())
    item.history = [{"at": datetime.now(timezone.utc).isoformat(), "status": item.status, "update": item.last_update}] if item.last_update else []
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@app.patch("/api/vendor-tickets/{ticket_id}")
def update_vendor_ticket(ticket_id: int, payload: VendorUpdate, session: Session = Depends(get_session)):
    item = session.get(VendorTicket, ticket_id)
    if item is None:
        raise HTTPException(404, "Vendor ticket not found")
    changes = payload.model_dump(exclude_none=True)
    previous_status = item.status
    previous_update = item.last_update
    status = changes.pop("status", None)
    latest_update = changes.pop("last_update", None)
    if status:
        item.status = status
    if latest_update is not None:
        item.last_update = latest_update
    if status != previous_status or (latest_update and latest_update != previous_update):
        item.history = [*item.history, {"at": datetime.now(timezone.utc).isoformat(), "status": item.status, "update": item.last_update}]
    for key, value in changes.items():
        setattr(item, key, value)
    item.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(item)
    return item


@app.get("/api/dashboards/overview")
def dashboard_overview(session: Session = Depends(get_session)):
    devices = session.scalars(select(InfrastructureDevice)).all()
    active_alerts = session.scalars(select(Alert).where(Alert.status != "resolved")).all()
    active_incidents = session.scalars(select(Incident).where(Incident.status.not_in(["resolved", "handoff complete"]))).all()
    return {"devices_total": len(devices), "devices_up": sum(item.status == "up" for item in devices), "devices_degraded": sum(item.status == "warning" for item in devices), "devices_critical": sum(item.status == "critical" for item in devices), "alerts_active": len(active_alerts), "alerts_critical": sum(item.severity == "critical" for item in active_alerts), "incidents_active": len(active_incidents), "vendors_open": session.scalar(select(func.count()).select_from(VendorTicket).where(VendorTicket.status != "resolved")) or 0, "game_status": "Doors open · 19:00 local", "updated_at": datetime.now(timezone.utc)}


@app.get("/api/dashboards/game-day")
def game_day(session: Session = Depends(get_session)):
    devices = session.scalars(select(InfrastructureDevice)).all()
    return {"venue": "Lakeshore Arena", "event": "Harbor City vs. Lakeview", "doors": "19:00 local", "event_status": "Pre-game operations", "critical_systems": [{"name": item.name, "category": item.category, "status": item.status} for item in devices if item.status != "up"], "network_ready_pct": round(100 * sum(item.status == "up" for item in devices) / max(1, len(devices)))}


@app.post("/api/monitoring/evaluate")
def evaluate_monitoring(payload: MonitoringEvaluate, session: Session = Depends(get_session)):
    devices = session.scalars(select(InfrastructureDevice)).all()
    candidates = evaluate_devices(devices, set(payload.alert_types) if payload.alert_types else None)
    created = []
    for candidate in candidates:
        duplicate = session.scalar(select(Alert).where(Alert.source == candidate["source"], Alert.title == candidate["title"], Alert.status != "resolved"))
        if duplicate is None:
            item = Alert(**candidate)
            session.add(item)
            created.append(item)
    session.commit()
    return {"evaluated": len(candidates), "created": len(created), "alerts": created}


@app.get("/api/cisco/commands")
def cisco_commands():
    return [{"command": "show interfaces status", "layer": "L1/L2", "purpose": "Port state, VLAN, duplex, and speed", "runbook": "https://www.cisco.com/c/en/us/support/docs/lan-switching/ethernet/"}, {"command": "show interfaces counters errors", "layer": "L1", "purpose": "CRC, input, output, and collision counters", "runbook": "https://www.cisco.com/c/en/us/support/docs/lan-switching/ethernet/"}, {"command": "show vlan brief", "layer": "L2", "purpose": "VLAN membership and active VLANs", "runbook": "https://www.cisco.com/c/en/us/support/docs/lan-switching/vlans/"}, {"command": "show spanning-tree", "layer": "L2", "purpose": "Root bridge, port roles, and topology state", "runbook": "https://www.cisco.com/c/en/us/support/docs/lan-switching/spanning-tree-protocol/"}, {"command": "show mac address-table", "layer": "L2", "purpose": "Learned MAC addresses and forwarding ports", "runbook": "https://www.cisco.com/c/en/us/support/docs/lan-switching/"}, {"command": "show cdp neighbors", "layer": "L2", "purpose": "Directly connected Cisco devices and interfaces", "runbook": "https://www.cisco.com/c/en/us/support/docs/lan-switching/cisco-discovery-protocol-cdp/"}, {"command": "show running-config interface <interface>", "layer": "L1/L2", "purpose": "Applied access, trunk, and interface settings", "runbook": "https://www.cisco.com/c/en/us/support/docs/lan-switching/"}, {"command": "show interfaces <interface>", "layer": "L1/L2", "purpose": "Physical state, line protocol, and error details", "runbook": "https://www.cisco.com/c/en/us/support/docs/lan-switching/ethernet/"}]


@app.post("/api/cisco/analyze")
def cisco_analyze(payload: CiscoAnalyze):
    return analyze_cli(payload.output)


@app.get("/api/reports/stakeholder-update")
def stakeholder_update(session: Session = Depends(get_session)):
    return stakeholder_summary(session.scalars(select(Incident).order_by(Incident.priority, Incident.created_at.desc())).all())


@app.get("/api/handoffs")
def handoffs(session: Session = Depends(get_session)):
    return session.scalars(select(Handoff).order_by(Handoff.created_at.desc())).all()


@app.get("/api/handoffs/trends")
def handoff_trends(session: Session = Depends(get_session)):
    saved = session.scalars(select(Handoff).order_by(Handoff.created_at.desc())).all()
    return build_handoff_trends(saved)


@app.post("/api/handoffs", status_code=201)
def create_handoff(payload: HandoffCreate, session: Session = Depends(get_session)):
    report = build_handoff(session.scalars(select(InfrastructureDevice)).all(), session.scalars(select(Alert)).all(), session.scalars(select(Incident)).all(), session.scalars(select(VendorTicket)).all())
    item = Handoff(operator=payload.operator, shift=payload.shift, report=report)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item
