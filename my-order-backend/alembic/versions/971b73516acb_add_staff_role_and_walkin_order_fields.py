"""add_staff_role_and_walkin_order_fields

Revision ID: 971b73516acb
Revises: b5e1f7c3a692
Create Date: 2026-08-23 19:50:12.299412

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '971b73516acb'
down_revision: Union[str, Sequence[str], None] = 'b5e1f7c3a692'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add 'staff' to UserRole enum
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'staff'")

    # Add walk-in order fields to orders table
    op.add_column('orders', sa.Column('created_by_staff_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('orders', sa.Column('is_walkin', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('orders', sa.Column('walkin_sender_name', sa.String(), nullable=True))
    op.add_column('orders', sa.Column('walkin_sender_phone', sa.String(), nullable=True))

    # Add foreign key constraint for created_by_staff_id
    op.create_foreign_key(
        'fk_orders_created_by_staff_id',
        'orders', 'users',
        ['created_by_staff_id'], ['id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop foreign key and columns
    op.drop_constraint('fk_orders_created_by_staff_id', 'orders', type_='foreignkey')
    op.drop_column('orders', 'walkin_sender_phone')
    op.drop_column('orders', 'walkin_sender_name')
    op.drop_column('orders', 'is_walkin')
    op.drop_column('orders', 'created_by_staff_id')

    # Note: Cannot remove 'staff' from enum in PostgreSQL without recreating the enum type
