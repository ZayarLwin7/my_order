import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class UserRole(str, enum.Enum):
    sender = "sender"
    rider = "rider"
    admin = "admin"
    staff = "staff"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    phone = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.sender)
    created_at = Column(DateTime, default=datetime.utcnow)
