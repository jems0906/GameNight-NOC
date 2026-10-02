IMPACT_ORDER = {"individual": 1, "department": 2, "multiple_departments": 3, "venue_wide": 4}
URGENCY_ORDER = {"low": 1, "normal": 2, "high": 3, "critical": 4}


def calculate_priority(impact: str, urgency: str) -> str:
    score = IMPACT_ORDER.get(impact, 2) + URGENCY_ORDER.get(urgency, 2)
    if score >= 7:
        return "P1"
    if score >= 6:
        return "P2"
    if score >= 4:
        return "P3"
    return "P4"


def build_handoff(devices: list, alerts: list, incidents: list, tickets: list) -> dict:
    active_incidents = [item for item in incidents if item.status != "handoff complete"]
    active_alerts = [item for item in alerts if item.status != "resolved"]
    open_tickets = [item for item in tickets if item.status != "resolved"]
    resolved = [item for item in incidents if item.status == "resolved"]
    return {
        "infrastructure_summary": {
            "total": len(devices),
            "degraded": [device.name for device in devices if device.status != "up"],
        },
        "open_incidents": [{"number": item.number, "title": item.title, "status": item.status, "priority": item.priority, "last_action": item.timeline[-1]["action"] if item.timeline else "No updates recorded"} for item in active_incidents],
        "active_alerts": [{"title": item.title, "severity": item.severity, "source": item.source} for item in active_alerts],
        "open_vendor_tickets": [{"provider": item.provider, "ticket_number": item.ticket_number, "status": item.status, "last_update": item.last_update} for item in open_tickets],
        "resolved_this_shift": [{"number": item.number, "title": item.title, "resolution": item.resolution} for item in resolved],
        "follow_up_actions": [f"Follow up with {item.provider} on {item.ticket_number}" for item in open_tickets],
    }


def build_handoff_trends(handoffs: list) -> dict:
    snapshots = []
    for handoff in reversed(handoffs):
        report = handoff.report or {}
        active_alerts = report.get("active_alerts", [])
        snapshots.append({
            "id": handoff.id,
            "created_at": handoff.created_at,
            "operator": handoff.operator,
            "shift": handoff.shift,
            "open_incidents": len(report.get("open_incidents", [])),
            "active_alerts": len(active_alerts),
            "critical_alerts": sum(alert.get("severity") == "critical" for alert in active_alerts),
            "degraded_systems": len(report.get("infrastructure_summary", {}).get("degraded", [])),
        })
    return {"count": len(snapshots), "snapshots": snapshots}


def stakeholder_summary(incidents: list) -> dict:
    active = [item for item in incidents if item.status not in {"resolved", "handoff complete"}]
    return {
        "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "updates": [{"incident": item.number, "issue": item.title, "impact": item.business_impact, "status": item.status.replace("_", " ").title(), "what_were_doing": item.timeline[-1]["action"] if item.timeline else "The operations team is investigating.", "estimated_resolution": "Assessment in progress"} for item in active],
    }


def analyze_cli(output: str) -> dict:
    text = output.lower()
    findings = []
    if "notconnect" in text or "down" in text:
        findings.append({"finding": "One or more interfaces appear down or not connected.", "next": "Check cabling and optics, then run show interfaces status and show interfaces <interface>."})
    if "crc" in text or "input error" in text or "collisions" in text:
        findings.append({"finding": "Physical-layer errors may indicate a cabling, optic, duplex, or speed issue.", "next": "Compare error counters at both ends and inspect the cable/optic before clearing counters."})
    if "err-disabled" in text:
        findings.append({"finding": "An interface is err-disabled and has been shut down by a protection feature.", "next": "Inspect the reason with show interfaces status and show errdisable recovery; correct the cause before recovery."})
    if "vlan" in text and ("mismatch" in text or "trunk" in text):
        findings.append({"finding": "VLAN or trunk configuration may not match the expected path.", "next": "Compare show vlan brief and show interfaces trunk on both switches."})
    if "root" in text and ("change" in text or "inconsistent" in text):
        findings.append({"finding": "Spanning-tree root or consistency behavior needs review.", "next": "Run show spanning-tree and verify the intended root bridge and port roles."})
    if not findings:
        findings.append({"finding": "No common error signature detected in the pasted output.", "next": "Gather show interfaces status, show interfaces counters errors, show vlan brief, and show spanning-tree for the affected switch."})
    return {"findings": findings, "disclaimer": "Suggestions are diagnostic starting points; verify against the approved change and network runbooks."}
