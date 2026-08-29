import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Numeric, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class ApplicationStatus(str, enum.Enum):
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"

class RiderProfile(Base):
    __tablename__ = "rider_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    nrc = Column(String, nullable=False)
    vehicle_plate = Column(String, nullable=False)
    photo_url = Column(String, nullable=True)
    wallet_balance = Column(Numeric(12, 2), default=0)
    application_status = Column(Enum(ApplicationStatus), default=ApplicationStatus.pending_review)
    active_status = Column(Boolean, default=False)
    suspended = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class RiderApplication(Base):
    __tablename__ = "rider_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    nrc = Column(String, nullable=False)
    license_number = Column(String, nullable=False)
    vehicle_plate = Column(String, nullable=False)
    photo_url = Column(String, nullable=True)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.pending_review)
    reviewer_notes = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
