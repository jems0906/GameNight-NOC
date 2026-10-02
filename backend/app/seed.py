from app.models import Alert, InfrastructureDevice, Incident, VendorTicket, utc_now


DEVICES = [
    {"name": "WAN-ARENA-PRI", "category": "Circuit", "location": "Network core", "address": "AT&T · CIR-CHI-4401", "status": "warning", "metrics": {"latency_ms": 42, "packet_loss_pct": 1.8, "provider": "AT&T"}},
    {"name": "WAN-ARENA-BACKUP", "category": "Circuit", "location": "Network core", "address": "Comcast · CIR-CHI-8820", "status": "up", "metrics": {"latency_ms": 18, "packet_loss_pct": 0, "provider": "Comcast"}},
    {"name": "CORE-SW-01", "category": "Switch", "location": "MDF · Level 1", "address": "10.20.0.11", "status": "up", "metrics": {"ports_up": 46, "ports_total": 48, "interface_errors": 0, "vlans": [10, 20, 30, 40]}},
    {"name": "CONCOURSE-SW-14", "category": "Switch", "location": "IDF · Section 114", "address": "10.20.14.14", "status": "warning", "metrics": {"ports_up": 22, "ports_total": 24, "interface_errors": 17, "vlans": [10, 20, 30]}},
    {"name": "AP-CLUB-07", "category": "Wireless AP", "location": "Founders Club", "address": "10.20.70.7", "status": "warning", "metrics": {"ssid": "Arena-Guest", "clients": 86, "signal_dbm": -71}},
    {"name": "AP-LOBBY-02", "category": "Wireless AP", "location": "Main lobby", "address": "10.20.70.2", "status": "up", "metrics": {"ssid": "Arena-Guest", "clients": 34, "signal_dbm": -54}},
    {"name": "TKT-SQL-01", "category": "Windows Server", "location": "Server room", "address": "10.20.10.21", "status": "critical", "metrics": {"cpu_pct": 94, "memory_pct": 88, "disk_pct": 72, "uptime": "42 days", "service": "TicketingSync: running"}},
    {"name": "AD-DC-02", "category": "Windows Server", "location": "Server room", "address": "10.20.10.12", "status": "up", "metrics": {"cpu_pct": 21, "memory_pct": 54, "disk_pct": 41, "uptime": "118 days", "service": "AD DS: running", "replication": "healthy"}},
    {"name": "VM-BROADCAST-INGEST", "category": "VMware VM", "location": "vSphere · Cluster A", "address": "10.20.30.41", "status": "up", "metrics": {"power_state": "On", "cpu_pct": 38, "memory_pct": 67, "vmware_tools": "Current"}},
    {"name": "BKUP-VM-DAILY", "category": "Backup Job", "location": "Backup cluster", "address": "Last run · 01:15 UTC", "status": "critical", "metrics": {"last_run": "01:15 UTC", "result": "Failed", "sla": "Missed · 04:00 UTC"}},
    {"name": "AD-REPLICATION", "category": "Active Directory", "location": "Domain · arena.local", "address": "DC-01 ↔ DC-02", "status": "up", "metrics": {"replication": "Healthy", "last_sync": "4 min ago"}},
]


def seed_database(session) -> None:
    if session.query(InfrastructureDevice).first():
        return
    now = utc_now()
    for data in DEVICES:
        session.add(InfrastructureDevice(**data, last_check=now))
    session.add_all([
        Alert(title="Ticketing database CPU above 90%", severity="critical", status="investigating", source="TKT-SQL-01", detail="CPU 94% for 12 minutes; ticketing sync latency increasing."),
        Alert(title="Primary circuit packet loss elevated", severity="warning", status="acknowledged", source="WAN-ARENA-PRI", detail="1.8% loss over the last 5-minute interval."),
        Alert(title="Backup job missed completion SLA", severity="critical", status="new", source="BKUP-VM-DAILY", detail="Nightly backup failed; recovery point objective at risk."),
        Alert(title="Founders Club AP client load high", severity="info", status="new", source="AP-CLUB-07", detail="86 clients connected; signal at -71 dBm."),
    ])
    session.add_all([
        Incident(number="INC-2408", title="Ticketing sync server under load", category="Compute", impact="multiple_departments", urgency="high", priority="P1", status="investigating", business_impact="Ticketing back-office sync is delayed; box-office sales are unaffected.", owner="M. Rivera", timeline=[{"at": now.isoformat(), "action": "Correlated CPU spike with the scheduled settlement export; reviewing process utilization."}]),
        Incident(number="INC-2407", title="Primary circuit intermittent packet loss", category="Network", impact="venue_wide", urgency="normal", priority="P2", status="vendor engaged", business_impact="Broadcast contribution path may experience intermittent degradation; backup circuit is healthy.", owner="J. Chen", timeline=[{"at": now.isoformat(), "action": "Failover path verified; provider ticket opened for upstream loss."}]),
        Incident(number="INC-2406", title="Nightly backup job failed", category="Backup", impact="department", urgency="normal", priority="P3", status="acknowledged", business_impact="Latest recovery point for the operations file share is older than target.", owner="A. Patel", timeline=[{"at": now.isoformat(), "action": "Confirmed repository capacity is available; retry queued after job log review."}]),
    ])
    session.add_all([
        VendorTicket(provider="AT&T", circuit_id="CIR-CHI-4401", ticket_number="ATT-982741", status="vendor investigating", contact="NOC · 1-800-555-0142", sla_target="Response due 03:30 UTC", last_update="Provider sees elevated errors at the west handoff; field team reviewing optical levels.", history=[{"at": now.isoformat(), "status": "vendor investigating", "update": "Provider sees elevated errors at the west handoff; field team reviewing optical levels."}]),
        VendorTicket(provider="Comcast Business", circuit_id="CIR-CHI-8820", ticket_number="CB-331058", status="awaiting vendor", contact="Enterprise desk · 1-800-555-0177", sla_target="Update due 04:00 UTC", last_update="Escalation submitted with interface counters and five-minute loss samples.", history=[{"at": now.isoformat(), "status": "awaiting vendor", "update": "Escalation submitted with interface counters and five-minute loss samples."}]),
    ])
    session.commit()
