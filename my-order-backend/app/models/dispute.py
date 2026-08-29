import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
from app.models.order import OrderStatus


class DisputeReason(str, enum.Enum):
    damaged = "damaged"
    missing = "missing"
    cod_mismatch = "cod_mismatch"
    other = "other"


class DisputeStatus(str, enum.Enum):
    open = "open"
    resolved = "resolved"


class ResolutionType(str, enum.Enum):
    full_refund = "full_refund"
    partial_refund = "partial_refund"
    wallet_adjustment = "wallet_adjustment"
    claim_denied = "claim_denied"


class RefundPayer(str, enum.Enum):
    partner = "partner"
    platform = "platform"
    rider = "rider"


class Dispute(Base):
    __tablename__ = "disputes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    filed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    reason = Column(Enum(DisputeReason), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(DisputeStatus), nullable=False, default=DisputeStatus.open)

    resolution_type = Column(Enum(ResolutionType), nullable=True)
    resolved_amount = Column(Numeric(12, 2), nullable=True)
    refund_payer = Column(Enum(RefundPayer), nullable=True)
    reviewer_notes = Column(Text, nullable=True)

    # so we can restore the order's status once the dispute is resolved
    order_status_before_dispute = Column(Enum(OrderStatus), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
