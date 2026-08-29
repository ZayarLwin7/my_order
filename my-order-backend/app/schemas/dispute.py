import uuid
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, model_validator
from app.models.dispute import DisputeReason, DisputeStatus, RefundPayer, ResolutionType


class DisputeCreate(BaseModel):
    order_id: uuid.UUID
    reason: DisputeReason
    description: str | None = None


class DisputeOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    filed_by_user_id: uuid.UUID
    reason: DisputeReason
    description: str | None
    status: DisputeStatus
    resolution_type: ResolutionType | None
    resolved_amount: Decimal | None
    refund_payer: RefundPayer | None
    reviewer_notes: str | None
    created_at: datetime
    resolved_at: datetime | None

    class Config:
        from_attributes = True


class DisputeResolveRequest(BaseModel):
    resolution_type: ResolutionType
    # Signed amount: refunds must be positive; wallet adjustments may be
    # negative (debit the rider) per the resolve endpoint's semantics.
    resolved_amount: Decimal | None = Field(default=None)
    refund_payer: RefundPayer | None = None
    reviewer_notes: str | None = None

    @model_validator(mode="after")
    def validate_amount_sign(self):
        if self.resolved_amount is not None:
            if self.resolution_type == ResolutionType.wallet_adjustment:
                if self.resolved_amount == 0:
                    raise ValueError("resolved_amount must be non-zero for a wallet adjustment")
            elif self.resolved_amount <= 0:
                raise ValueError("resolved_amount must be positive for refund resolutions")
        return self
