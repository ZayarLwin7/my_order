"""create delivery pricing and quotes

Revision ID: a3c8d5e2f941
Revises: 9f1b4a6d2e70
Create Date: 2026-08-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a3c8d5e2f941"
down_revision: Union[str, Sequence[str], None] = "9f1b4a6d2e70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("delivery_zones",
        sa.Column("id", sa.UUID(), nullable=False), sa.Column("city", sa.String(), nullable=False),
        sa.Column("township", sa.String(), nullable=False), sa.Column("surcharge_mmk", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("city", "township", name="uq_delivery_zone_city_township"))
    op.create_table("item_size_rates",
        sa.Column("id", sa.UUID(), nullable=False), sa.Column("name", sa.String(), nullable=False),
        sa.Column("surcharge_mmk", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("name"))
    op.create_table("delivery_quotes",
        sa.Column("id", sa.UUID(), nullable=False), sa.Column("sender_id", sa.UUID(), nullable=False), sa.Column("order_id", sa.UUID(), nullable=True),
        sa.Column("delivery_mode", sa.String(), nullable=False), sa.Column("destination_city", sa.String(), nullable=True),
        sa.Column("destination_township", sa.String(), nullable=True), sa.Column("destination_town", sa.String(), nullable=True),
        sa.Column("dropoff_address", sa.String(), nullable=True), sa.Column("dropoff_lat", sa.Numeric(10, 7), nullable=True), sa.Column("dropoff_lng", sa.Numeric(10, 7), nullable=True),
        sa.Column("terminal_name", sa.String(), nullable=True), sa.Column("bus_line", sa.String(), nullable=True), sa.Column("fee_payer", sa.String(), nullable=False),
        sa.Column("base_fee_mmk", sa.Numeric(12, 2), nullable=False), sa.Column("zone_surcharge_mmk", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("partner_discount_mmk", sa.Numeric(12, 2), nullable=False, server_default="0"), sa.Column("estimated_fee_mmk", sa.Numeric(12, 2), nullable=False),
        sa.Column("final_item_size", sa.String(), nullable=True), sa.Column("final_item_size_surcharge_mmk", sa.Numeric(12, 2), nullable=True), sa.Column("final_fee_mmk", sa.Numeric(12, 2), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]), sa.ForeignKeyConstraint(["sender_id"], ["users.id"]), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("order_id"))
    op.add_column("partner_profiles", sa.Column("delivery_discount_mmk", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.add_column("orders", sa.Column("quote_id", sa.UUID(), nullable=True))
    op.add_column("orders", sa.Column("price_confirmed_at", sa.DateTime(), nullable=True))
    op.alter_column("orders", "item_size", existing_type=sa.String(), nullable=True)
    op.create_foreign_key("fk_orders_quote_id", "orders", "delivery_quotes", ["quote_id"], ["id"])
    op.create_unique_constraint("uq_orders_quote_id", "orders", ["quote_id"])


def downgrade() -> None:
    op.drop_constraint("uq_orders_quote_id", "orders", type_="unique")
    op.drop_constraint("fk_orders_quote_id", "orders", type_="foreignkey")
    op.alter_column("orders", "item_size", existing_type=sa.String(), nullable=False)
    op.drop_column("orders", "price_confirmed_at")
    op.drop_column("orders", "quote_id")
    op.drop_column("partner_profiles", "delivery_discount_mmk")
    op.drop_table("delivery_quotes")
    op.drop_table("item_size_rates")
    op.drop_table("delivery_zones")
