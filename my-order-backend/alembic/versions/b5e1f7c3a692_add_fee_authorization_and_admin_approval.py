"""add fee authorization and admin approval

Revision ID: b5e1f7c3a692
Revises: a3c8d5e2f941
Create Date: 2026-08-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b5e1f7c3a692"
down_revision: Union[str, Sequence[str], None] = "a3c8d5e2f941"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("delivery_quotes", sa.Column("maximum_fee_mmk", sa.Numeric(12, 2), nullable=True))
    op.execute("UPDATE delivery_quotes SET maximum_fee_mmk = estimated_fee_mmk WHERE maximum_fee_mmk IS NULL")
    op.alter_column("delivery_quotes", "maximum_fee_mmk", existing_type=sa.Numeric(12, 2), nullable=False)
    op.add_column("orders", sa.Column("authorized_max_fee_mmk", sa.Numeric(12, 2), nullable=True))
    op.add_column("orders", sa.Column("price_approved_by_admin_id", sa.UUID(), nullable=True))
    op.add_column("orders", sa.Column("price_approval_note", sa.Text(), nullable=True))
    op.create_foreign_key("fk_orders_price_approved_by_admin", "orders", "users", ["price_approved_by_admin_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_orders_price_approved_by_admin", "orders", type_="foreignkey")
    op.drop_column("orders", "price_approval_note")
    op.drop_column("orders", "price_approved_by_admin_id")
    op.drop_column("orders", "authorized_max_fee_mmk")
    op.drop_column("delivery_quotes", "maximum_fee_mmk")
