import argparse
import json
import urllib.error
import urllib.request


DEFAULT_TYPES = "circuit_loss,switch_port,wireless_load,server_cpu,server_disk,service_down,backup_failure,ad_replication,vmware_tools,device_status"


def main():
    parser = argparse.ArgumentParser(description="Evaluate selected synthetic venue monitoring rules through the GameNight NOC API.")
    parser.add_argument("--api-url", default="http://localhost:8000", help="Backend base URL")
    parser.add_argument("--types", default=DEFAULT_TYPES, help="Comma-separated rule types")
    args = parser.parse_args()
    payload = json.dumps({"alert_types": [value.strip() for value in args.types.split(",") if value.strip()]}).encode()
    request = urllib.request.Request(f"{args.api_url.rstrip('/')}/api/monitoring/evaluate", data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            print(json.dumps(json.load(response), indent=2))
    except urllib.error.URLError as error:
        raise SystemExit(f"Could not reach NOC API: {error}") from error


if __name__ == "__main__":
    main()
