import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class RiderEarningStatus(str, enum.Enum):
    available = "available"
    processing = "processing"
    paid = "paid"


class RiderPayoutStatus(str, enum.Enum):
    pending_payment = "pending_payment"
    paid = "paid"
    failed = "failed"


class RiderCompensationRate(Base):
    __tablename__ = "rider_compensation_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    per_completed_way_mmk = Column(Numeric(12, 2), nullable=False)
    effective_from = Column(Date, nullable=False, unique=True)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class RiderPayout(Base):
    __tablename__ = "rider_payouts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rider_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    salary_amount = Column(Numeric(12, 2), nullable=False, default=0)
    per_way_amount = Column(Numeric(12, 2), nullable=False, default=0)
    total_amount = Column(Numeric(12, 2), nullable=False)
    status = Column(Enum(RiderPayoutStatus), nullable=False, default=RiderPayoutStatus.pending_payment)
    payment_reference = Column(String, nullable=True, unique=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)


class RiderEarning(Base):
    __tablename__ = "rider_earnings"
    __table_args__ = (UniqueConstraint("order_id", name="uq_rider_earnings_order_id"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rider_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    payout_id = Column(UUID(as_uuid=True), ForeignKey("rider_payouts.id"), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(Enum(RiderEarningStatus), nullable=False, default=RiderEarningStatus.available)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
