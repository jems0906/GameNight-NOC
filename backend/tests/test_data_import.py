import csv

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.data_import import import_csv_samples
from app.database import Base
from app.models import InfrastructureDevice


def test_csv_import_upserts_circuit_rows(tmp_path):
    path = tmp_path / "network_circuits.csv"
    with path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=["provider", "circuit_id", "name", "status", "latency_ms", "packet_loss_pct"])
        writer.writeheader()
        writer.writerow({"provider": "Test Provider", "circuit_id": "CIR-1", "name": "WAN-TEST", "status": "warning", "latency_ms": "36", "packet_loss_pct": "1.1"})

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        assert import_csv_samples(session, tmp_path)["devices"] == 1
        assert import_csv_samples(session, tmp_path)["devices"] == 1
        device = session.scalar(select(InfrastructureDevice).where(InfrastructureDevice.name == "WAN-TEST"))
        assert device.metrics["latency_ms"] == 36.0
        assert session.scalar(select(InfrastructureDevice.id).where(InfrastructureDevice.name == "WAN-TEST")) is not None
    engine.dispose()
