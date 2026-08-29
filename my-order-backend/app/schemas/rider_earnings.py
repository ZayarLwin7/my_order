import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.rider_earnings import RiderEarningStatus, RiderPayoutStatus


class RiderCompensationRateCreate(BaseModel):
    per_completed_way_mmk: Decimal = Field(gt=0)
    effective_from: date


class RiderCompensationRateOut(BaseModel):
    id: uuid.UUID
    per_completed_way_mmk: Decimal
    effective_from: date
    created_at: datetime

    class Config:
        from_attributes = True


class RiderEarningOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    payout_id: uuid.UUID | None
    amount: Decimal
    status: RiderEarningStatus
    note: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class RiderEarningsSummary(BaseModel):
    available_amount: Decimal
    processing_amount: Decimal
    paid_amount: Decimal


class RiderPayoutCreate(BaseModel):
    rider_user_id: uuid.UUID
    period_start: date
    period_end: date
    salary_amount: Decimal = Field(default=Decimal("0"), ge=0)
    note: str | None = None


class RiderPayoutPaymentRequest(BaseModel):
    payment_reference: str = Field(min_length=1, max_length=128)
    note: str | None = None


class RiderPayoutFailureRequest(BaseModel):
    note: str


class RiderPayoutOut(BaseModel):
    id: uuid.UUID
    rider_user_id: uuid.UUID
    period_start: date
    period_end: date
    salary_amount: Decimal
    per_way_amount: Decimal
    total_amount: Decimal
    status: RiderPayoutStatus
    payment_reference: str | None
    note: str | None
    created_at: datetime
    paid_at: datetime | None

    class Config:
        from_attributes = True
