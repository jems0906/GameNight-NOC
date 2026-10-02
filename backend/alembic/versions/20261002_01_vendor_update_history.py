"""Add timestamped vendor update history.

Revision ID: 20261002_01
Revises:
Create Date: 2026-10-02
"""

from alembic import op
import sqlalchemy as sa

from app.database import Base
from app import models

revision = "20261002_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("vendor_tickets"):
        Base.metadata.create_all(bind=bind)
        inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("vendor_tickets")}
    if "history" not in columns:
        op.add_column("vendor_tickets", sa.Column("history", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("vendor_tickets") and "history" in {column["name"] for column in inspector.get_columns("vendor_tickets")}:
        with op.batch_alter_table("vendor_tickets") as batch:
            batch.drop_column("history")
