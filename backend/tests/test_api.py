import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.main import app, get_session
from app.seed import seed_database


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    test_sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_session():
        session = test_sessions()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_session
    with test_sessions() as session:
        seed_database(session)
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_health_and_inventory(client):
    assert client.get("/api/health").json()["status"] == "ok"
    assert len(client.get("/api/infrastructure").json()) >= 10


def test_create_incident_from_alert(client):
    response = client.post("/api/alerts/1/incident")
    assert response.status_code == 201
    incident = response.json()
    assert incident["title"] == "Ticketing database CPU above 90%"
    assert incident["priority"] == "P2"
    alerts = client.get("/api/alerts").json()
    source_alert = next(alert for alert in alerts if alert["title"] == incident["title"])
    assert source_alert["status"] == "acknowledged"


def test_incident_action_is_preserved_in_timeline(client):
    incident_id = client.get("/api/incidents").json()[0]["id"]
    response = client.patch(f"/api/incidents/{incident_id}", json={"action": "Compared uplink counters with the core switch."})
    assert response.status_code == 200
    assert response.json()["timeline"][-1]["action"] == "Compared uplink counters with the core switch."


def test_monitoring_evaluation_suppresses_open_duplicates(client):
    first = client.post("/api/monitoring/evaluate", json={"alert_types": ["circuit_loss"]}).json()
    second = client.post("/api/monitoring/evaluate", json={"alert_types": ["circuit_loss"]}).json()
    assert first["evaluated"] == 1
    assert first["created"] == 1
    assert second["evaluated"] == 1
    assert second["created"] == 0


def test_handoff_saves_current_incident_snapshot(client):
    response = client.post("/api/handoffs", json={"operator": "Test Operator", "shift": "Overnight"})
    assert response.status_code == 201
    handoff = response.json()
    assert handoff["operator"] == "Test Operator"
    assert len(handoff["report"]["open_incidents"]) == 3
    assert len(client.get("/api/handoffs").json()) == 1


def test_handoff_trends_summarize_saved_reports(client):
    client.post("/api/handoffs", json={"operator": "Trend Test", "shift": "Overnight"})
    response = client.get("/api/handoffs/trends")
    assert response.status_code == 200
    trend = response.json()["snapshots"][0]
    assert trend["operator"] == "Trend Test"
    assert trend["open_incidents"] == 3
    assert trend["critical_alerts"] == 2


def test_vendor_updates_retain_timestamped_history(client):
    ticket = client.get("/api/vendor-tickets").json()[0]
    response = client.patch(f"/api/vendor-tickets/{ticket['id']}", json={"status": "vendor investigating", "last_update": "Provider confirmed field escalation."})
    assert response.status_code == 200
    updated = response.json()
    assert updated["history"][-1]["status"] == "vendor investigating"
    assert updated["history"][-1]["update"] == "Provider confirmed field escalation."
    assert updated["history"][-1]["at"]
