import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from alembic import command
from alembic.config import Config
from app.data_import import import_csv_samples
from app.database import Base, SessionLocal, engine
from app import models


def main():
    parser = argparse.ArgumentParser(description="Import the provided CSV samples into the configured GameNight NOC database.")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data_samples", help="Directory containing CSV files")
    args = parser.parse_args()
    Base.metadata.create_all(bind=engine)
    command.upgrade(Config(str(BACKEND / "alembic.ini")), "head")
    with SessionLocal() as session:
        counts = import_csv_samples(session, args.data_dir.resolve())
    print("Imported sample rows:", counts)


if __name__ == "__main__":
    main()
