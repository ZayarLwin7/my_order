import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.order import OrderStatus, DeliveryMode


class TrackingMilestone(BaseModel):
    status: OrderStatus
    note: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class TrackingOut(BaseModel):
    order_id: uuid.UUID
    delivery_mode: DeliveryMode
    recipient_name: str
    current_status: OrderStatus
    terminal_name: str | None
    bus_line: str | None
    milestones: list[TrackingMilestone]
