import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class DeliveryZone(Base):
    __tablename__ = "delivery_zones"
    __table_args__ = (UniqueConstraint("city", "township", name="uq_delivery_zone_city_township"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    city = Column(String, nullable=False)
    township = Column(String, nullable=False)
    surcharge_mmk = Column(Numeric(12, 2), nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ItemSizeRate(Base):
    __tablename__ = "item_size_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    surcharge_mmk = Column(Numeric(12, 2), nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class DeliveryQuote(Base):
    __tablename__ = "delivery_quotes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), unique=True, nullable=True)
    delivery_mode = Column(String, nullable=False)
    destination_city = Column(String, nullable=True)
    destination_township = Column(String, nullable=True)
    destination_town = Column(String, nullable=True)
    dropoff_address = Column(String, nullable=True)
    dropoff_lat = Column(Numeric(10, 7), nullable=True)
    dropoff_lng = Column(Numeric(10, 7), nullable=True)
    terminal_name = Column(String, nullable=True)
    bus_line = Column(String, nullable=True)
    fee_payer = Column(String, nullable=False, default="sender")
    base_fee_mmk = Column(Numeric(12, 2), nullable=False)
    zone_surcharge_mmk = Column(Numeric(12, 2), nullable=False, default=0)
    partner_discount_mmk = Column(Numeric(12, 2), nullable=False, default=0)
    estimated_fee_mmk = Column(Numeric(12, 2), nullable=False)
    maximum_fee_mmk = Column(Numeric(12, 2), nullable=False)
    final_item_size = Column(String, nullable=True)
    final_item_size_surcharge_mmk = Column(Numeric(12, 2), nullable=True)
    final_fee_mmk = Column(Numeric(12, 2), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
