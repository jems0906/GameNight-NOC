# Cisco Layer 1 / Layer 2 Troubleshooting

1. Confirm the affected device, interface, user impact, and change window. Capture current output before changing configuration.
2. Run `show interfaces status` to identify link state, VLAN, speed, and duplex. Compare the expected access/trunk mode.
3. Run `show interfaces <interface>` and `show interfaces counters errors`. Rising CRC/input errors often point to cabling, optics, or duplex issues; compare both ends before resetting counters.
4. Run `show vlan brief` and `show interfaces trunk` to confirm the VLAN exists and is allowed on the path.
5. Run `show spanning-tree` to verify root bridge, port roles, and blocked/inconsistent state. Do not change STP settings without the network change process.
6. Run `show mac address-table` to verify endpoint learning and `show cdp neighbors` to map the adjacent Cisco device.
7. Inspect `show running-config interface <interface>` for access VLAN, trunk allow-list, speed/duplex, and error-disable configuration.
8. Record commands, timestamps, before/after counters, business impact, and rollback or escalation details in the incident timeline.

Do not paste secrets, public IPs, customer information, or unredacted configurations into the demo analyzer. The analyzer is heuristic and makes no device connections.
