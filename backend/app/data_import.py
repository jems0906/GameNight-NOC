import csv
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Alert, Handoff, Incident, InfrastructureDevice, VendorTicket, utc_now
from app.services import calculate_priority


def _rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as source:
        return list(csv.DictReader(source))


def _number(value: str | None, cast=float, default=0):
    try:
        return cast(value) if value not in (None, "") else default
    except (TypeError, ValueError):
        return default


def _device(session: Session, name: str, category: str, location: str, address: str, status: str, metrics: dict) -> None:
    item = session.scalar(select(InfrastructureDevice).where(InfrastructureDevice.name == name))
    if item is None:
        item = InfrastructureDevice(name=name, category=category)
        session.add(item)
    item.category = category
    item.location = location or "Venue"
    item.address = address or ""
    item.status = status.lower() or "up"
    item.metrics = metrics
    item.last_check = utc_now()


def import_csv_samples(session: Session, data_dir: Path) -> dict[str, int]:
    counts: dict[str, int] = {}

    for row in _rows(data_dir / "network_circuits.csv"):
        name = row.get("name") or row.get("circuit_id", "")
        _device(session, name, "Circuit", "Network core", row.get("circuit_id", ""), row.get("status", "up"), {"provider": row.get("provider", ""), "latency_ms": _number(row.get("latency_ms")), "packet_loss_pct": _number(row.get("packet_loss_pct"))})
        counts["devices"] = counts.get("devices", 0) + 1

    for row in _rows(data_dir / "cisco_switches.csv"):
        name = row.get("hostname", "")
        vlans = [_number(value, int) for value in row.get("vlans", "").replace(",", ";").split(";") if value.strip()]
        _device(session, name, "Switch", row.get("location", "Venue"), row.get("ip", ""), row.get("status", "up"), {"ports_up": _number(row.get("ports_up"), int), "ports_total": _number(row.get("ports_total"), int), "interface_errors": _number(row.get("interface_errors"), int), "vlans": vlans})
        counts["devices"] = counts.get("devices", 0) + 1

    for row in _rows(data_dir / "wireless_aps.csv"):
        name = row.get("hostname", "")
        _device(session, name, "Wireless AP", row.get("location", "Venue"), row.get("ip", ""), row.get("status", "up"), {"ssid": row.get("ssid", ""), "clients": _number(row.get("clients"), int), "signal_dbm": _number(row.get("signal_dbm"), int, -55)})
        counts["devices"] = counts.get("devices", 0) + 1

    for row in _rows(data_dir / "windows_servers.csv"):
        name = row.get("hostname", "")
        _device(session, name, "Windows Server", row.get("role", "Server room"), row.get("ip", ""), row.get("status", "up"), {"cpu_pct": _number(row.get("cpu_pct")), "memory_pct": _number(row.get("memory_pct")), "disk_pct": _number(row.get("disk_pct")), "uptime": row.get("uptime", ""), "service": row.get("service", "")})
        counts["devices"] = counts.get("devices", 0) + 1

    for row in _rows(data_dir / "vmware_vms.csv"):
        name = row.get("vm_name", "")
        _device(session, name, "VMware VM", row.get("cluster", "vSphere"), row.get("cluster", ""), row.get("status", "up"), {"power_state": row.get("power_state", "Unknown"), "cpu_pct": _number(row.get("cpu_pct")), "memory_pct": _number(row.get("memory_pct")), "vmware_tools": row.get("vmware_tools", "Unknown")})
        counts["devices"] = counts.get("devices", 0) + 1

    for row in _rows(data_dir / "backup_jobs.csv"):
        name = row.get("job_name", "")
        _device(session, name, "Backup Job", "Backup cluster", row.get("last_run", ""), row.get("status", "up"), {"last_run": row.get("last_run", ""), "result": row.get("result", "Unknown"), "sla": row.get("sla", "")})
        counts["devices"] = counts.get("devices", 0) + 1

    for row in _rows(data_dir / "solarwinds_alerts.csv"):
        title, source = row.get("title", ""), row.get("source", "")
        item = session.scalar(select(Alert).where(Alert.title == title, Alert.source == source))
        if item is None:
            item = Alert(title=title, source=source)
            session.add(item)
        item.severity = row.get("severity", "info").lower()
        item.status = row.get("status", "new").lower()
        item.detail = row.get("detail", "")
        counts["alerts"] = counts.get("alerts", 0) + 1

    for row in _rows(data_dir / "incidents.csv"):
        number = row.get("number", "")
        item = session.scalar(select(Incident).where(Incident.number == number))
        impact = row.get("impact", "department").lower()
        urgency = row.get("urgency", "normal").lower()
        if item is None:
            item = Incident(number=number, title=row.get("title", ""))
            session.add(item)
            item.timeline = [{"at": utc_now().isoformat(), "action": "Imported from CSV sample"}]
        item.title = row.get("title", item.title)
        item.category = row.get("category", "Infrastructure")
        item.impact = impact
        item.urgency = urgency
        item.priority = row.get("priority") or calculate_priority(impact, urgency)
        item.status = row.get("status", "new").lower()
        item.owner = row.get("owner", "Night Operations")
        item.business_impact = row.get("business_impact", "")
        counts["incidents"] = counts.get("incidents", 0) + 1

    for row in _rows(data_dir / "vendor_tickets.csv"):
        number = row.get("ticket_number", "")
        item = session.scalar(select(VendorTicket).where(VendorTicket.ticket_number == number))
        if item is None:
            item = VendorTicket(ticket_number=number)
            session.add(item)
        item.provider = row.get("provider", "")
        item.circuit_id = row.get("circuit_id", "")
        item.status = row.get("status", "open").lower()
        item.contact = row.get("contact", "")
        item.sla_target = row.get("sla_target", "")
        update = row.get("last_update", "")
        if update and update != item.last_update:
            item.history = [*item.history, {"at": utc_now().isoformat(), "status": item.status, "update": update}]
            item.last_update = update
        counts["vendor_tickets"] = counts.get("vendor_tickets", 0) + 1

    for row in _rows(data_dir / "synthetic_infrastructure.csv"):
        try:
            metrics = json.loads(row.get("metrics", "{}"))
        except json.JSONDecodeError:
            metrics = {}
        _device(session, row.get("name", ""), row.get("category", "Infrastructure"), row.get("location", "Venue"), row.get("address", ""), row.get("status", "up"), metrics)
        counts["devices"] = counts.get("devices", 0) + 1

    session.commit()
    return counts
