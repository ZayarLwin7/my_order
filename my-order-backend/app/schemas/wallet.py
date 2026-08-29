import uuid
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.wallet import TransactionType


class WalletOut(BaseModel):
    rider_user_id: uuid.UUID
    wallet_balance: Decimal
    active_status: bool
    suspended: bool
    alert: bool  # true if balance exceeds configured threshold


class WalletTransactionOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID | None
    type: TransactionType
    amount: Decimal
    reference: str | None
    note: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class SuspendRequest(BaseModel):
    suspended: bool
    reason: str | None = None


class RemittanceRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    reference: str = Field(min_length=1, max_length=128)
    note: str | None = None


class RemittanceAllocationItem(BaseModel):
    order_id: uuid.UUID
    cod_amount: Decimal = Field(default=Decimal("0"), ge=0)
    delivery_fee_amount: Decimal = Field(default=Decimal("0"), ge=0)


class RemittanceAllocationRequest(BaseModel):
    allocations: list[RemittanceAllocationItem] = Field(min_length=1)


class RemittanceAllocationOut(BaseModel):
    id: uuid.UUID
    remittance_transaction_id: uuid.UUID
    order_id: uuid.UUID
    cod_amount: Decimal
    delivery_fee_amount: Decimal
    created_at: datetime

    class Config:
        from_attributes = True
