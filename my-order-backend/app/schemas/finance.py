import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.partner import PlatformLedgerEntryType


class PlatformLedgerEntryOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID | None
    rider_user_id: uuid.UUID | None
    partner_user_id: uuid.UUID | None
    settlement_id: uuid.UUID | None
    type: PlatformLedgerEntryType
    amount: Decimal
    note: str | None
    created_at: datetime

    class Config:
        from_attributes = True
