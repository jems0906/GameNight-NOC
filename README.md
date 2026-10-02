# GameNight NOC

A portfolio-ready Network Operations Center dashboard for overnight IT operations at a professional sports venue. The app simulates infrastructure monitoring, alert triage, incident response, external provider coordination, Cisco switch troubleshooting, business updates, and shift handoff.

## Run locally

Requirements: Python 3.11+ and Node.js 20+.

```powershell
# Terminal 1: backend
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 2: frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The API applies Alembic migrations and seeds a simulated venue inventory on first startup; local SQLite data is stored in `backend/gamenight.db`. API documentation is at http://localhost:8000/docs. No external monitoring system is contacted; all telemetry and incidents are synthetic.

## Local containers

```sh
docker compose up --build
```

Open http://localhost:8080. The compose stack runs PostgreSQL, the API, and the production-built frontend. `DATABASE_URL` defaults to local SQLite when running the API directly; set it to the Railway PostgreSQL connection string or the compose service URL for PostgreSQL.

## Main workflows

- Overview and game-day readiness summarize device status, circuit latency, active alerts, incidents, and provider cases.
- Infrastructure inventory covers network circuits, Cisco switches, wireless APs, Windows servers, VMware VMs, backup jobs, and Active Directory health.
- Alert queue advances alerts through new, acknowledged, investigating, and resolved; alert status changes are retained in history. Alerts can be converted to incidents.
- Incidents calculate P1–P4 priority from impact and urgency and retain timestamped troubleshooting actions and resolution notes.
- Vendor tickets track provider ticket numbers, contacts, circuit IDs, updates, and SLA targets.
- Cisco toolkit lists common IOS commands and analyzes pasted output for common Layer 1/Layer 2 signatures. Treat suggestions as diagnostic starting points, not automated fixes.
- Shift handoffs are generated from current data, saved to the database, and printable/searchable by shift history.
- Stakeholder updates translate current incident status and business impact into plain language.

## Seed and import data

From the repository root, seed the built-in demo records or import the provided CSV samples (imports are idempotent upserts):

```sh
python scripts/seed_database.py
python scripts/import_all.py
```

Generate a repeatable synthetic inventory CSV and import it:

```sh
python scripts/generate_infra_data.py --count 28 --seed 42
python scripts/import_all.py
```

By default, the generator writes `data_samples/synthetic_infrastructure.csv`; `import_all.py --data-dir <path>` can import from another directory. Run `alembic upgrade head` from `backend/` to explicitly apply schema migrations. The API also applies pending migrations during startup.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Readiness check |
| GET | `/api/dashboards/overview`, `/api/dashboards/game-day` | Dashboard summary |
| GET | `/api/infrastructure` | Inventory and latest health |
| GET/PATCH | `/api/alerts`, `/api/alerts/{id}` | Alert queue and lifecycle |
| POST | `/api/alerts/{id}/incident` | Create an incident from an alert |
| POST/PATCH/GET | `/api/incidents` | Incident lifecycle and notes |
| GET/POST/PATCH | `/api/vendor-tickets` | Vendor coordination |
| POST | `/api/monitoring/evaluate` | Evaluate selected synthetic threshold rules |
| GET/POST | `/api/handoffs` | Generate and search saved handoffs |
| GET | `/api/handoffs/trends` | Per-shift incident, alert, and degraded-system snapshots |
| GET | `/api/cisco/commands` | Cisco IOS reference |
| POST | `/api/cisco/analyze` | Analyze pasted CLI output |
| GET | `/api/reports/stakeholder-update` | Plain-language status summary |

## Synthetic monitoring

Evaluate all default rules against the seeded metrics:

```sh
python scripts/generate_synthetic_alerts.py
```

Select rule types with `--types circuit_loss,server_cpu,backup_failure`. Supported types are `circuit_loss`, `switch_port`, `wireless_load`, `server_cpu`, `server_disk`, `service_down`, `backup_failure`, `ad_replication`, `vmware_tools`, and `device_status`. Open duplicate alerts are suppressed.

## Tests and build

```sh
cd backend
python -m pytest
cd ../frontend
npm run build
```

## Railway deployment

Railway IaC is defined in `.railway/railway.ts` for the `jems0906/GameNight-NOC` repository on `main`. It creates one PostgreSQL database and two GitHub-connected services rooted at `backend/` and `frontend/`. It references Railway-generated database and public-domain variables; no database credentials are stored in this repository.

After pushing changes to GitHub and authenticating with the Railway CLI:

```sh
npm install
railway init --name GameNight-NOC
railway config plan
railway config apply
railway domain --service backend --port 8000
railway domain --service frontend --port 8080
```

Review the plan before applying. It should create `postgres`, `backend`, and `frontend`. The IaC references set backend `DATABASE_URL` from the managed database, backend `CORS_ORIGINS` from the frontend public domain, and frontend `VITE_API_URL` from the backend public domain. The frontend URL is a Vite build-time variable, so allow its deployment to rebuild after domains are created. Verify the backend `/api/health` endpoint and then open the frontend domain.

Railway credentials remain in Railway-managed variables. If a Railway project already exists, link it with `railway link` and inspect `railway config plan` carefully before applying changes.
