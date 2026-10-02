from app.models import utc_now


RULE_CATEGORIES = {
    "circuit_loss": "Circuit",
    "switch_port": "Switch",
    "wireless_load": "Wireless AP",
    "server_cpu": "Windows Server",
    "server_disk": "Windows Server",
    "service_down": "Windows Server",
    "backup_failure": "Backup Job",
    "ad_replication": "Active Directory",
    "vmware_tools": "VMware VM",
    "device_status": None,
}


def evaluate_devices(devices: list, selected_types: set[str] | None = None) -> list[dict]:
    candidates = []
    for device in devices:
        metrics = device.metrics or {}
        normalized_status = device.status.lower()
        service_status = str(metrics.get("service", "")).lower()
        service_stopped = any(term in service_status for term in ("stopped", "not running", "failed", "down"))
        checks = {
            "device_status": (normalized_status in {"critical", "down", "offline"}, "critical", f"{device.name} is reporting {normalized_status} status"),
            "circuit_loss": (metrics.get("packet_loss_pct", 0) >= 0.5, "critical" if metrics.get("packet_loss_pct", 0) >= 2 else "warning", f"{device.name} packet loss above threshold"),
            "switch_port": (metrics.get("interface_errors", 0) >= 10 or metrics.get("ports_up", 0) < metrics.get("ports_total", 0), "warning", f"{device.name} switch port condition needs review"),
            "wireless_load": (metrics.get("clients", 0) >= 80 or metrics.get("signal_dbm", -50) <= -70, "warning", f"{device.name} wireless client load or signal degraded"),
            "server_cpu": (metrics.get("cpu_pct", 0) >= 85, "critical" if metrics.get("cpu_pct", 0) >= 90 else "warning", f"{device.name} CPU utilization above threshold"),
            "server_disk": (metrics.get("disk_pct", 0) >= 85, "critical" if metrics.get("disk_pct", 0) >= 95 else "warning", f"{device.name} disk utilization above threshold"),
            "service_down": (service_stopped, "critical", f"{device.name} critical service is stopped"),
            "backup_failure": (str(metrics.get("result", "")).lower() in {"failed", "error"}, "critical", f"{device.name} backup job failed"),
            "ad_replication": (str(metrics.get("replication", "")).lower() not in {"", "healthy", "ok"}, "warning", f"{device.name} replication status needs review"),
            "vmware_tools": (metrics.get("vmware_tools") not in {None, "Current"}, "warning", f"{device.name} VMware Tools status needs review"),
        }
        for rule_type, (triggered, severity, title) in checks.items():
            category = RULE_CATEGORIES[rule_type]
            if not triggered or (selected_types is not None and rule_type not in selected_types):
                continue
            if category and device.category != category:
                continue
            detail = f"Rule {rule_type} triggered for {device.name}; metrics: {metrics}."
            candidates.append({"title": title, "severity": severity, "status": "new", "source": device.name, "detail": detail, "created_at": utc_now()})
    return candidates
