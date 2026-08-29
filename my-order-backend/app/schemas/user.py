import uuid
import enum
from pydantic import BaseModel, ConfigDict, Field
from app.models.user import UserRole


class PublicRegistrationRole(str, enum.Enum):
    sender = "sender"
    rider = "rider"


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=6, max_length=32, pattern=r"^\+?[0-9][0-9 -]*$")
    password: str = Field(min_length=12, max_length=72)
    role: PublicRegistrationRole = PublicRegistrationRole.sender

class UserOut(BaseModel):
    id: uuid.UUID
    name: str
    phone: str
    role: UserRole

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=72)
