"""create remittance allocations

Revision ID: 8e2c6f93a45d
Revises: 7d4f8a20bc31
Create Date: 2026-08-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8e2c6f93a45d"
down_revision: Union[str, Sequence[str], None] = "7d4f8a20bc31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rider_remittance_allocations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("remittance_transaction_id", sa.UUID(), nullable=False),
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("cod_amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"),
        sa.Column("delivery_fee_amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"),
        sa.Column("allocated_by_user_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("cod_amount >= 0", name="ck_remittance_allocation_cod_nonnegative"),
        sa.CheckConstraint("delivery_fee_amount >= 0", name="ck_remittance_allocation_fee_nonnegative"),
        sa.CheckConstraint("cod_amount + delivery_fee_amount > 0", name="ck_remittance_allocation_nonzero"),
        sa.ForeignKeyConstraint(["allocated_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["remittance_transaction_id"], ["wallet_transactions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_remittance_allocations_remittance", "rider_remittance_allocations", ["remittance_transaction_id"])
    op.create_index("ix_remittance_allocations_order", "rider_remittance_allocations", ["order_id"])
    # Existing merchant credits must be explicitly reconciled before a new payout.
    op.execute("UPDATE partner_ledger_entries SET status = 'on_hold' WHERE type = 'cod_credit' AND status = 'available'")


def downgrade() -> None:
    op.drop_index("ix_remittance_allocations_order", table_name="rider_remittance_allocations")
    op.drop_index("ix_remittance_allocations_remittance", table_name="rider_remittance_allocations")
    op.drop_table("rider_remittance_allocations")
