import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.partner import (
    PartnerApplicationStatus,
    PartnerLedgerEntryStatus,
    PartnerLedgerEntryType,
    PartnerSettlementStatus,
)


class PartnerApplicationCreate(BaseModel):
    business_name: str
    business_address: str
    contact_phone: str


class PartnerApplicationOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    business_name: str
    business_address: str
    contact_phone: str
    status: PartnerApplicationStatus
    reviewer_notes: str | None
    submitted_at: datetime
    reviewed_at: datetime | None

    class Config:
        from_attributes = True


class PartnerReviewRequest(BaseModel):
    reviewer_notes: str | None = None


class PartnerLedgerEntryOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    settlement_id: uuid.UUID | None
    type: PartnerLedgerEntryType
    amount: Decimal
    status: PartnerLedgerEntryStatus
    note: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class PartnerSettlementCreate(BaseModel):
    partner_user_id: uuid.UUID
    period_start: date
    period_end: date
    note: str | None = None


class PartnerSettlementPaymentRequest(BaseModel):
    mmqr_reference: str
    note: str | None = None


class PartnerSettlementFailureRequest(BaseModel):
    note: str


class PartnerSettlementOut(BaseModel):
    id: uuid.UUID
    partner_user_id: uuid.UUID
    period_start: date
    period_end: date
    total_amount: Decimal
    status: PartnerSettlementStatus
    mmqr_reference: str | None
    note: str | None
    created_at: datetime
    paid_at: datetime | None

    class Config:
        from_attributes = True


class PartnerPayoutMethodRequest(BaseModel):
    mmqr_account_name: str
    mmqr_account_reference: str


class PartnerSuspendRequest(BaseModel):
    suspended: bool
    note: str | None = None


class PartnerSettlementSummary(BaseModel):
    available_amount: Decimal
    on_hold_amount: Decimal
    processing_amount: Decimal
    paid_amount: Decimal
