import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.rider import ApplicationStatus

class RiderApplicationCreate(BaseModel):
    nrc: str
    license_number: str
    vehicle_plate: str
    photo_url: str | None = None

class RiderApplicationOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    nrc: str
    license_number: str
    vehicle_plate: str
    status: ApplicationStatus
    submitted_at: datetime

    class Config:
        from_attributes = True

class RiderReviewRequest(BaseModel):
    reviewer_notes: str | None = None


class ActiveRiderOut(BaseModel):
    """Assignable rider summary for admin order-assignment dropdowns."""
    user_id: uuid.UUID
    name: str
    phone: str


class RiderSummaryOut(BaseModel):
    """Admin list-view summary for a rider (application + profile state)."""
    user_id: uuid.UUID
    name: str
    phone: str
    application_status: ApplicationStatus
    active_status: bool
    suspended: bool

    class Config:
        from_attributes = True
