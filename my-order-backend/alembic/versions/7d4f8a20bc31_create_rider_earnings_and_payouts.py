"""create rider earnings and payouts

Revision ID: 7d4f8a20bc31
Revises: 6a7c0e29d14b
Create Date: 2026-08-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7d4f8a20bc31"
down_revision: Union[str, Sequence[str], None] = "6a7c0e29d14b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rider_compensation_rates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("per_completed_way_mmk", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("created_by_user_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("effective_from"),
    )
    op.create_table(
        "rider_payouts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("rider_user_id", sa.UUID(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("salary_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("per_way_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("status", sa.Enum("pending_payment", "paid", "failed", name="riderpayoutstatus"), nullable=False),
        sa.Column("payment_reference", sa.String(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["rider_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payment_reference"),
    )
    op.create_index("ix_rider_payouts_rider_user_id", "rider_payouts", ["rider_user_id"])
    op.create_table(
        "rider_earnings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("rider_user_id", sa.UUID(), nullable=False),
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("payout_id", sa.UUID(), nullable=True),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("status", sa.Enum("available", "processing", "paid", name="riderearningstatus"), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["payout_id"], ["rider_payouts.id"]),
        sa.ForeignKeyConstraint(["rider_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id", name="uq_rider_earnings_order_id"),
    )
    op.create_index("ix_rider_earnings_rider_status_created", "rider_earnings", ["rider_user_id", "status", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_rider_earnings_rider_status_created", table_name="rider_earnings")
    op.drop_table("rider_earnings")
    op.drop_index("ix_rider_payouts_rider_user_id", table_name="rider_payouts")
    op.drop_table("rider_payouts")
    op.drop_table("rider_compensation_rates")
