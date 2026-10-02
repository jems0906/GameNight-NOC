import argparse
import csv
import json
import random
from pathlib import Path


CATEGORIES = [
    ("Circuit", "WAN", {"latency_ms": 22, "packet_loss_pct": 0.0, "provider": "AT&T"}),
    ("Switch", "SW", {"ports_up": 46, "ports_total": 48, "interface_errors": 0, "vlans": [10, 20, 30]}),
    ("Wireless AP", "AP", {"ssid": "Arena-Guest", "clients": 24, "signal_dbm": -55}),
    ("Windows Server", "SRV", {"cpu_pct": 32, "memory_pct": 56, "disk_pct": 48, "uptime": "31 days", "service": "TicketingSync: running"}),
    ("VMware VM", "VM", {"power_state": "On", "cpu_pct": 28, "memory_pct": 53, "vmware_tools": "Current"}),
    ("Backup Job", "BKUP", {"last_run": "02:00 UTC", "result": "Success", "sla": "Met"}),
    ("Active Directory", "AD", {"replication": "Healthy", "last_sync": "4 min ago"}),
]


def main():
    parser = argparse.ArgumentParser(description="Generate a reproducible synthetic venue infrastructure inventory CSV.")
    parser.add_argument("--count", type=int, default=21, help="Number of synthetic devices to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for repeatable output")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "data_samples" / "synthetic_infrastructure.csv")
    args = parser.parse_args()
    if args.count < 1 or args.count > 5000:
        parser.error("--count must be between 1 and 5000")

    rng = random.Random(args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=["name", "category", "location", "address", "status", "metrics"])
        writer.writeheader()
        for index in range(1, args.count + 1):
            category, prefix, metrics = CATEGORIES[(index - 1) % len(CATEGORIES)]
            values = dict(metrics)
            if category == "Circuit":
                values["latency_ms"] = rng.randint(12, 45)
                values["packet_loss_pct"] = round(rng.choice([0, 0, 0.1, 0.4, 1.2]), 1)
            elif category == "Switch":
                values["interface_errors"] = rng.choice([0, 0, 1, 3, 12])
            elif category == "Wireless AP":
                values["clients"] = rng.randint(8, 95)
                values["signal_dbm"] = rng.randint(-78, -42)
            elif category == "Windows Server":
                values["cpu_pct"] = rng.randint(18, 96)
                values["memory_pct"] = rng.randint(32, 92)
                values["disk_pct"] = rng.randint(35, 96)
            status = "critical" if (category == "Windows Server" and values.get("cpu_pct", 0) >= 90) else "warning" if rng.random() < 0.18 else "up"
            writer.writerow({"name": f"{prefix}-VENUE-{index:03d}", "category": category, "location": f"Venue zone {((index - 1) % 12) + 1:02d}", "address": f"10.30.{index // 250}.{(index % 250) + 1}", "status": status, "metrics": json.dumps(values, separators=(",", ":"))})
    print(f"Wrote {args.count} synthetic devices to {args.output}")


if __name__ == "__main__":
    main()
