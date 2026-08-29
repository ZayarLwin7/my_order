import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Numeric, Boolean, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class OrderStatus(str, enum.Enum):
    pending = "pending"
    assigned = "assigned"
    picked_up = "picked_up"
    delivered = "delivered"
    dropped_at_terminal = "dropped_at_terminal"
    delivery_failed = "delivery_failed"
    disputed = "disputed"
    cancelled = "cancelled"
    cancelled_post_pickup = "cancelled_post_pickup"
    returned = "returned"


class DeliveryMode(str, enum.Enum):
    door_to_door = "door_to_door"
    bus_terminal = "bus_terminal"


class FeePayer(str, enum.Enum):
    sender = "sender"
    recipient = "recipient"


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    rider_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Walk-in order support (staff creates order on behalf of walk-in customer)
    created_by_staff_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_walkin = Column(Boolean, nullable=False, default=False)
    walkin_sender_name = Column(String, nullable=True)
    walkin_sender_phone = Column(String, nullable=True)

    delivery_mode = Column(Enum(DeliveryMode), nullable=False)
    quote_id = Column(UUID(as_uuid=True), ForeignKey("delivery_quotes.id"), unique=True, nullable=True)

    recipient_name = Column(String, nullable=False)
    recipient_phone = Column(String, nullable=False)

    pickup_address = Column(String, nullable=False)
    pickup_lat = Column(Float, nullable=False)
    pickup_lng = Column(Float, nullable=False)

    dropoff_address = Column(String, nullable=True)
    dropoff_lat = Column(Float, nullable=True)
    dropoff_lng = Column(Float, nullable=True)

    terminal_name = Column(String, nullable=True)
    bus_line = Column(String, nullable=True)

    item_size = Column(String, nullable=True)
    item_value = Column(Numeric(12, 2), nullable=False)
    cod_amount = Column(Numeric(12, 2), nullable=False, default=0)
    delivery_fee = Column(Numeric(12, 2), nullable=False)
    authorized_max_fee_mmk = Column(Numeric(12, 2), nullable=True)
    price_confirmed_at = Column(DateTime, nullable=True)
    price_approved_by_admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    price_approval_note = Column(Text, nullable=True)
    fee_payer = Column(Enum(FeePayer), nullable=False)

    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.pending)
    terms_accepted = Column(Boolean, nullable=False, default=False)

    cancel_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sender = relationship("User", foreign_keys=[sender_id])
    rider = relationship("User", foreign_keys=[rider_id])
    created_by_staff = relationship("User", foreign_keys=[created_by_staff_id])


class OrderTrackingLog(Base):
    __tablename__ = "order_tracking_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    status = Column(Enum(OrderStatus), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
