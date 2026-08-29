import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.order import DeliveryMode, FeePayer


class DeliveryZoneUpsert(BaseModel):
    city: str = Field(min_length=1, max_length=80)
    township: str = Field(min_length=1, max_length=80)
    surcharge_mmk: Decimal = Field(ge=0)
    active: bool = True


class DeliveryZoneOut(DeliveryZoneUpsert):
    id: uuid.UUID

    class Config:
        from_attributes = True


class ItemSizeRateUpsert(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    surcharge_mmk: Decimal = Field(ge=0)
    active: bool = True


class ItemSizeRateOut(ItemSizeRateUpsert):
    id: uuid.UUID

    class Config:
        from_attributes = True


class DeliveryQuoteCreate(BaseModel):
    delivery_mode: DeliveryMode
    destination_city: str | None = None
    destination_township: str | None = None
    destination_town: str | None = None
    dropoff_address: str | None = None
    dropoff_lat: float | None = None
    dropoff_lng: float | None = None
    terminal_name: str | None = None
    bus_line: str | None = None
    fee_payer: FeePayer = FeePayer.sender

    @model_validator(mode="after")
    def validate_destination(self):
        if self.delivery_mode == DeliveryMode.door_to_door:
            if not self.destination_city or not self.destination_township or not self.dropoff_address or self.dropoff_lat is None or self.dropoff_lng is None:
                raise ValueError("city, township, and drop-off address/coordinates are required for Door-to-Door")
        elif not self.destination_town or not self.terminal_name or not self.bus_line:
            raise ValueError("destination_town, terminal_name, and bus_line are required for Bus Terminal")
        return self


class DeliveryQuoteOut(BaseModel):
    id: uuid.UUID
    delivery_mode: DeliveryMode
    destination_city: str | None
    destination_township: str | None
    destination_town: str | None
    dropoff_address: str | None
    dropoff_lat: Decimal | None
    dropoff_lng: Decimal | None
    terminal_name: str | None
    bus_line: str | None
    fee_payer: FeePayer
    base_fee_mmk: Decimal
    zone_surcharge_mmk: Decimal
    partner_discount_mmk: Decimal
    estimated_fee_mmk: Decimal
    maximum_fee_mmk: Decimal
    final_item_size: str | None
    final_item_size_surcharge_mmk: Decimal | None
    final_fee_mmk: Decimal | None
    expires_at: datetime

    class Config:
        from_attributes = True


class PartnerDiscountRequest(BaseModel):
    delivery_discount_mmk: Decimal = Field(ge=0)
