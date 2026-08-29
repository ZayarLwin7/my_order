"""create partner sender tables

Revision ID: 4c2bf1d9564a
Revises: 270180dcb20b
Create Date: 2026-08-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4c2bf1d9564a"
down_revision: Union[str, Sequence[str], None] = "270180dcb20b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "partner_applications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("business_name", sa.String(), nullable=False),
        sa.Column("business_address", sa.String(), nullable=False),
        sa.Column("contact_phone", sa.String(), nullable=False),
        sa.Column("status", sa.Enum("pending_review", "approved", "rejected", name="partnerapplicationstatus"), nullable=False),
        sa.Column("reviewer_notes", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_partner_applications_user_id", "partner_applications", ["user_id"])
    op.create_table(
        "partner_profiles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("business_name", sa.String(), nullable=False),
        sa.Column("business_address", sa.String(), nullable=False),
        sa.Column("contact_phone", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("partner_profiles")
    op.drop_index("ix_partner_applications_user_id", table_name="partner_applications")
    op.drop_table("partner_applications")
