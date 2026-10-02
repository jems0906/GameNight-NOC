from types import SimpleNamespace

from app.services import analyze_cli, build_handoff, build_handoff_trends, calculate_priority


def test_priority_matrix():
    assert calculate_priority("venue_wide", "critical") == "P1"
    assert calculate_priority("individual", "low") == "P4"


def test_cli_analysis_flags_crc_errors():
    result = analyze_cli("Gi1/0/1  12 CRC errors, input errors")
    assert "physical-layer" in result["findings"][0]["finding"].lower()
    assert "counters at both ends" in result["findings"][0]["next"]


def test_handoff_captures_open_and_resolved_work():
    open_incident = SimpleNamespace(number="INC-1", title="Circuit loss", status="investigating", priority="P2", timeline=[{"action": "Failover verified"}], resolution="")
    resolved_incident = SimpleNamespace(number="INC-2", title="AP reboot", status="resolved", priority="P3", timeline=[], resolution="Rebooted AP")
    report = build_handoff([], [], [open_incident, resolved_incident], [])
    assert report["open_incidents"][0]["last_action"] == "Failover verified"
    assert report["resolved_this_shift"][0]["resolution"] == "Rebooted AP"


def test_handoff_trends_count_alerts_and_degraded_assets():
    handoff = SimpleNamespace(id=1, operator="Morgan", shift="Overnight", created_at="2026-10-02T03:00:00Z", report={"open_incidents": [{"number": "INC-1"}], "active_alerts": [{"severity": "critical"}, {"severity": "warning"}], "infrastructure_summary": {"degraded": ["WAN-1"]}})
    trends = build_handoff_trends([handoff])
    assert trends["count"] == 1
    assert trends["snapshots"][0]["critical_alerts"] == 1
    assert trends["snapshots"][0]["degraded_systems"] == 1
