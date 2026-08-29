"""add financial controls

Revision ID: 6a7c0e29d14b
Revises: 5b8f3d78a01e
Create Date: 2026-08-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "6a7c0e29d14b"
down_revision: Union[str, Sequence[str], None] = "5b8f3d78a01e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("partner_profiles", sa.Column("active_status", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("partner_profiles", sa.Column("suspended", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("partner_profiles", sa.Column("mmqr_account_name", sa.String(), nullable=True))
    op.add_column("partner_profiles", sa.Column("mmqr_account_reference", sa.String(), nullable=True))
    op.add_column("partner_profiles", sa.Column("payout_verified_at", sa.DateTime(), nullable=True))
    op.add_column("partner_profiles", sa.Column("payout_verified_by_user_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_partner_profiles_payout_verified_by_user_id",
        "partner_profiles",
        "users",
        ["payout_verified_by_user_id"],
        ["id"],
    )
    op.add_column("partner_ledger_entries", sa.Column("available_at", sa.DateTime(), nullable=True))
    op.execute("UPDATE partner_ledger_entries SET available_at = created_at WHERE available_at IS NULL")
    refund_payer = postgresql.ENUM("partner", "platform", "rider", name="refundpayer")
    refund_payer.create(op.get_bind(), checkfirst=True)
    op.add_column("disputes", sa.Column("refund_payer", refund_payer, nullable=True))
    op.add_column("wallet_transactions", sa.Column("reference", sa.String(), nullable=True))
    op.create_unique_constraint("uq_wallet_transactions_reference", "wallet_transactions", ["reference"])
    op.create_table(
        "platform_ledger_entries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("order_id", sa.UUID(), nullable=True),
        sa.Column("rider_user_id", sa.UUID(), nullable=True),
        sa.Column("partner_user_id", sa.UUID(), nullable=True),
        sa.Column("settlement_id", sa.UUID(), nullable=True),
        sa.Column("type", sa.Enum("delivery_fee_revenue", "rider_remittance", "partner_payout", "customer_refund", "rider_refund_recovery", name="platformledgerentrytype"), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["rider_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["partner_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["settlement_id"], ["partner_settlements.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("settlement_id"),
    )
    op.create_index("ix_platform_ledger_entries_created_at", "platform_ledger_entries", ["created_at"])
    op.create_index("ix_platform_ledger_entries_order_id", "platform_ledger_entries", ["order_id"])


def downgrade() -> None:
    op.drop_index("ix_platform_ledger_entries_order_id", table_name="platform_ledger_entries")
    op.drop_index("ix_platform_ledger_entries_created_at", table_name="platform_ledger_entries")
    op.drop_table("platform_ledger_entries")
    op.drop_constraint("uq_wallet_transactions_reference", "wallet_transactions", type_="unique")
    op.drop_column("wallet_transactions", "reference")
    op.drop_column("disputes", "refund_payer")
    op.drop_column("partner_ledger_entries", "available_at")
    op.drop_constraint("fk_partner_profiles_payout_verified_by_user_id", "partner_profiles", type_="foreignkey")
    op.drop_column("partner_profiles", "payout_verified_by_user_id")
    op.drop_column("partner_profiles", "payout_verified_at")
    op.drop_column("partner_profiles", "mmqr_account_reference")
    op.drop_column("partner_profiles", "mmqr_account_name")
    op.drop_column("partner_profiles", "suspended")
    op.drop_column("partner_profiles", "active_status")
