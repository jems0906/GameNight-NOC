# Synthetic Alert Rules

| Rule key | Category | Trigger | Default severity |
| --- | --- | --- | --- |
| `circuit_loss` | Circuit | Packet loss >= 0.5%; critical at >= 2% | Warning / critical |
| `switch_port` | Switch | Interface errors >= 10 or ports below expected total | Warning |
| `wireless_load` | Wireless AP | Clients >= 80 or signal <= -70 dBm | Warning |
| `server_cpu` | Windows Server | CPU >= 85%; critical at >= 90% | Warning / critical |
| `server_disk` | Windows Server | Disk >= 85%; critical at >= 95% | Warning / critical |
| `service_down` | Windows Server | Service text reports stopped, not running, failed, or down | Critical |
| `backup_failure` | Backup Job | Result is failed or error | Critical |
| `ad_replication` | Active Directory | Replication state is not healthy | Warning |
| `vmware_tools` | VMware VM | Tools state is not current | Warning |
| `device_status` | Any device | Device status is critical, down, or offline | Critical |

Call `POST /api/monitoring/evaluate` with `{"alert_types":["server_cpu","circuit_loss"]}`. Omit `alert_types` to evaluate all. The evaluator suppresses duplicate unresolved alerts with the same source and title. These are demonstration thresholds and should be tuned to approved production baselines.
