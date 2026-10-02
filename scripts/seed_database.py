from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from alembic import command
from alembic.config import Config
from app.database import Base, SessionLocal, engine
from app import models
from app.seed import seed_database


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    command.upgrade(Config(str(BACKEND / "alembic.ini")), "head")
    with SessionLocal() as session:
        seed_database(session)
    print("GameNight NOC demo data is ready.")
