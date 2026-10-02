# Architecture

## Services

- **React/Vite frontend**: operational pages, TanStack Table inventory, Recharts network trend, and typed-by-convention JSON API client. In development, Vite proxies `/api` to FastAPI. Production static assets are served by nginx; `VITE_API_URL` is a build-time public API origin.
- **FastAPI backend**: REST workflows, validation, monitoring-rule evaluation, Cisco output triage, priority calculation, handoff generation, and stakeholder report generation.
- **SQLAlchemy persistence**: PostgreSQL in Railway/Compose; SQLite is the zero-setup local default. SQLAlchemy creates the demo schema at startup and seeds it only when the inventory is empty.

## Data flow

The API reads inventory and operational records into dashboard summaries. Synthetic monitoring rules evaluate stored device metrics and create alerts while suppressing duplicate unresolved alerts. An alert can be advanced or converted into an incident. Incidents retain a JSON timeline and calculated priority. Handoffs snapshot open incidents, active alerts, provider cases, resolved work, and degraded asset names into a persistent report.

## Deployment boundaries

The frontend is static and does not connect to the database. The API owns database access and must receive `DATABASE_URL`. Configure `CORS_ORIGINS` to include the deployed frontend origin. `VITE_API_URL` must be set at frontend build time. PostgreSQL credentials and public domains belong in Railway variables, not source control.

## Demo limitations

This project uses seeded synthetic inventory and a short in-process rule evaluator. It does not poll SolarWinds, Cisco devices, VMware, Active Directory, backup infrastructure, or provider systems. CLI analysis is heuristic and never executes commands. Production adoption would require authentication, role-based access, audit retention, migrations, durable task scheduling, and connectors to approved monitoring sources.
