"""add financial idempotency constraints

Revision ID: 9f1b4a6d2e70
Revises: 8e2c6f93a45d
Create Date: 2026-08-20
"""
from typing import Sequence, Union

from alembic import op


revision: str = "9f1b4a6d2e70"
down_revision: Union[str, Sequence[str], None] = "8e2c6f93a45d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # One completed order can produce exactly one rider cash-collection entry
    # and exactly one partner COD credit. Refund adjustments remain repeatable.
    op.execute(
        "CREATE UNIQUE INDEX uq_wallet_collection_per_order "
        "ON wallet_transactions (order_id) WHERE type = 'collection'"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_partner_cod_credit_per_order "
        "ON partner_ledger_entries (order_id) WHERE type = 'cod_credit'"
    )


def downgrade() -> None:
    op.execute("DROP INDEX uq_partner_cod_credit_per_order")
    op.execute("DROP INDEX uq_wallet_collection_per_order")
