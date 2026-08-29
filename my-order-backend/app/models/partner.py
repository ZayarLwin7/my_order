import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class PartnerApplicationStatus(str, enum.Enum):
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"


class PartnerApplication(Base):
    __tablename__ = "partner_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    business_name = Column(String, nullable=False)
    business_address = Column(String, nullable=False)
    contact_phone = Column(String, nullable=False)
    status = Column(Enum(PartnerApplicationStatus), nullable=False, default=PartnerApplicationStatus.pending_review)
    reviewer_notes = Column(Text, nullable=True)
    submitted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

    user = relationship("User", foreign_keys=[user_id])


class PartnerProfile(Base):
    __tablename__ = "partner_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    business_name = Column(String, nullable=False)
    business_address = Column(String, nullable=False)
    contact_phone = Column(String, nullable=False)
    active_status = Column(Boolean, nullable=False, default=True)
    suspended = Column(Boolean, nullable=False, default=False)
    delivery_discount_mmk = Column(Numeric(12, 2), nullable=False, default=0)
    mmqr_account_name = Column(String, nullable=True)
    mmqr_account_reference = Column(String, nullable=True)
    payout_verified_at = Column(DateTime, nullable=True)
    payout_verified_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])


class PartnerLedgerEntryType(str, enum.Enum):
    cod_credit = "cod_credit"
    refund_adjustment = "refund_adjustment"


class PartnerLedgerEntryStatus(str, enum.Enum):
    available = "available"
    on_hold = "on_hold"
    processing = "processing"
    paid = "paid"


class PartnerSettlementStatus(str, enum.Enum):
    pending_payment = "pending_payment"
    paid = "paid"
    failed = "failed"


class PartnerSettlement(Base):
    __tablename__ = "partner_settlements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    status = Column(Enum(PartnerSettlementStatus), nullable=False, default=PartnerSettlementStatus.pending_payment)
    mmqr_reference = Column(String, nullable=True, unique=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)


class PartnerLedgerEntry(Base):
    __tablename__ = "partner_ledger_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    settlement_id = Column(UUID(as_uuid=True), ForeignKey("partner_settlements.id"), nullable=True)
    type = Column(Enum(PartnerLedgerEntryType), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(Enum(PartnerLedgerEntryStatus), nullable=False, default=PartnerLedgerEntryStatus.available)
    available_at = Column(DateTime, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class PlatformLedgerEntryType(str, enum.Enum):
    delivery_fee_revenue = "delivery_fee_revenue"
    rider_remittance = "rider_remittance"
    partner_payout = "partner_payout"
    customer_refund = "customer_refund"
    rider_refund_recovery = "rider_refund_recovery"


class PlatformLedgerEntry(Base):
    __tablename__ = "platform_ledger_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    rider_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    partner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    settlement_id = Column(UUID(as_uuid=True), ForeignKey("partner_settlements.id"), nullable=True, unique=True)
    type = Column(Enum(PlatformLedgerEntryType), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
