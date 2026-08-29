import uuid
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.order import OrderStatus, DeliveryMode, FeePayer


class OrderCreate(BaseModel):
    quote_id: uuid.UUID
    recipient_name: str
    recipient_phone: str

    pickup_address: str
    pickup_lat: float
    pickup_lng: float

    item_value: Decimal = Field(gt=0)
    cod_amount: Decimal = Field(default=Decimal("0"), ge=0)
    authorized_max_fee_mmk: Decimal = Field(ge=0)
    terms_accepted: bool


class WalkinOrderCreate(BaseModel):
    """Schema for staff creating orders on behalf of walk-in customers"""
    quote_id: uuid.UUID

    # Walk-in customer (sender) details
    walkin_sender_name: str = Field(min_length=1, max_length=200)
    walkin_sender_phone: str = Field(min_length=7, max_length=20)

    # Recipient details
    recipient_name: str
    recipient_phone: str

    pickup_address: str
    pickup_lat: float
    pickup_lng: float

    item_value: Decimal = Field(gt=0)
    cod_amount: Decimal = Field(default=Decimal("0"), ge=0)
    authorized_max_fee_mmk: Decimal = Field(ge=0)
    terms_accepted: bool


class OrderOut(BaseModel):
    id: uuid.UUID
    quote_id: uuid.UUID | None
    sender_id: uuid.UUID
    rider_id: uuid.UUID | None

    # Walk-in order fields
    created_by_staff_id: uuid.UUID | None
    is_walkin: bool
    walkin_sender_name: str | None
    walkin_sender_phone: str | None

    delivery_mode: DeliveryMode
    recipient_name: str
    recipient_phone: str
    pickup_address: str
    dropoff_address: str | None
    terminal_name: str | None
    bus_line: str | None
    item_size: str | None
    item_value: Decimal
    cod_amount: Decimal
    delivery_fee: Decimal
    authorized_max_fee_mmk: Decimal | None
    price_confirmed_at: datetime | None
    fee_payer: FeePayer
    status: OrderStatus
    created_at: datetime

    class Config:
        from_attributes = True


class OrderAssignRequest(BaseModel):
    rider_id: uuid.UUID


class OrderStatusUpdateRequest(BaseModel):
    status: OrderStatus
    note: str | None = None


class OrderCancelRequest(BaseModel):
    reason: str | None = None


class OrderItemSizeVerifyRequest(BaseModel):
    item_size: str


class OrderAdminFeeApprovalRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
