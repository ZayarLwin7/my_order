"""create partner ledger and settlements

Revision ID: 5b8f3d78a01e
Revises: 4c2bf1d9564a
Create Date: 2026-08-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5b8f3d78a01e"
down_revision: Union[str, Sequence[str], None] = "4c2bf1d9564a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "partner_settlements",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("partner_user_id", sa.UUID(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("status", sa.Enum("pending_payment", "paid", "failed", name="partnersettlementstatus"), nullable=False),
        sa.Column("mmqr_reference", sa.String(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["partner_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mmqr_reference"),
    )
    op.create_index("ix_partner_settlements_partner_user_id", "partner_settlements", ["partner_user_id"])
    op.create_table(
        "partner_ledger_entries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("partner_user_id", sa.UUID(), nullable=False),
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("settlement_id", sa.UUID(), nullable=True),
        sa.Column("type", sa.Enum("cod_credit", "refund_adjustment", name="partnerledgerentrytype"), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("status", sa.Enum("available", "on_hold", "processing", "paid", name="partnerledgerentrystatus"), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["partner_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["settlement_id"], ["partner_settlements.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_partner_ledger_entries_partner_status_created", "partner_ledger_entries", ["partner_user_id", "status", "created_at"])
    op.create_index("ix_partner_ledger_entries_order_id", "partner_ledger_entries", ["order_id"])


def downgrade() -> None:
    op.drop_index("ix_partner_ledger_entries_order_id", table_name="partner_ledger_entries")
    op.drop_index("ix_partner_ledger_entries_partner_status_created", table_name="partner_ledger_entries")
    op.drop_table("partner_ledger_entries")
    op.drop_index("ix_partner_settlements_partner_user_id", table_name="partner_settlements")
    op.drop_table("partner_settlements")
