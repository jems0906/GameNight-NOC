"""Backfill provider history from the current ticket state.

Revision ID: 20261002_02
Revises: 20261002_01
Create Date: 2026-10-02
"""

from alembic import op
import sqlalchemy as sa

revision = "20261002_02"
down_revision = "20261002_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("vendor_tickets"):
        return
    tickets = sa.Table("vendor_tickets", sa.MetaData(), autoload_with=bind)
    rows = bind.execute(sa.select(tickets.c.id, tickets.c.status, tickets.c.last_update, tickets.c.updated_at, tickets.c.history)).mappings()
    for ticket in rows:
        if ticket["history"] or not ticket["last_update"]:
            continue
        bind.execute(sa.update(tickets).where(tickets.c.id == ticket["id"]).values(history=[{
            "at": str(ticket["updated_at"]),
            "status": ticket["status"],
            "update": ticket["last_update"],
        }]))


def downgrade() -> None:
    pass
