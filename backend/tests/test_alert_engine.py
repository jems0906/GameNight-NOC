from types import SimpleNamespace

from app.monitoring.alert_engine import evaluate_devices


def test_rules_respect_selected_alert_types():
    device = SimpleNamespace(name="WAN-1", category="Circuit", status="warning", metrics={"packet_loss_pct": 1.2})
    assert len(evaluate_devices([device], {"circuit_loss"})) == 1
    assert evaluate_devices([device], {"server_cpu"}) == []


def test_critical_device_status_generates_alert():
    device = SimpleNamespace(name="SRV-1", category="Windows Server", status="critical", metrics={"cpu_pct": 96})
    alerts = evaluate_devices([device], {"device_status"})
    assert alerts[0]["severity"] == "critical"
    assert alerts[0]["source"] == "SRV-1"


def test_offline_access_point_generates_device_status_alert():
    device = SimpleNamespace(name="AP-1", category="Wireless AP", status="offline", metrics={})
    alerts = evaluate_devices([device], {"device_status"})
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "critical"


def test_stopped_windows_service_generates_critical_alert():
    device = SimpleNamespace(name="SRV-2", category="Windows Server", status="up", metrics={"service": "TicketingSync: stopped"})
    alerts = evaluate_devices([device], {"service_down"})
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "critical"
