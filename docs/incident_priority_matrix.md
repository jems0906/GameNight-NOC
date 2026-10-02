# Incident Priority Matrix

Priority is derived from impact score plus urgency score. P1 is the highest priority.

| Impact / urgency | Low (1) | Normal (2) | High (3) | Critical (4) |
| --- | --- | --- | --- | --- |
| Individual (1) | P4 | P4 | P3 | P3 |
| Department (2) | P4 | P3 | P3 | P2 |
| Multiple departments (3) | P3 | P3 | P2 | P1 |
| Venue-wide (4) | P3 | P2 | P1 | P1 |

The implementation uses thresholds: score 7+ is P1, 6 is P2, 4–5 is P3, and 2–3 is P4. Operators should validate business impact and urgency; calculated priority is a starting point, not a substitute for incident command judgment.
