import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.user import User, UserRole
from app.models.partner import PartnerApplication, PartnerApplicationStatus, PartnerProfile
from app.models.rider import RiderApplication, RiderProfile, ApplicationStatus

router = APIRouter(prefix="/users", tags=["Users"])


class MeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    phone: str
    role: UserRole

    # Merchant/partner state (senders)
    partner_status: str  # none | pending_review | approved | rejected
    partner_business_name: str | None = None
    is_active_partner: bool = False

    # Rider application state (riders)
    rider_status: str = "none"  # none | pending_review | approved | rejected
    is_active_rider: bool = False


def _partner_state(db: Session, user_id: uuid.UUID) -> tuple[str, str | None, bool]:
    """Derive partner status from profile + application records."""
    profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == user_id).first()
    if profile:
        # A suspended or deactivated approved partner still reports "approved"
        # so the UI can show account-specific messaging rather than re-applying.
        return "approved", profile.business_name, profile.active_status and not profile.suspended

    application = (
        db.query(PartnerApplication)
        .filter(
            PartnerApplication.user_id == user_id,
            PartnerApplication.status == PartnerApplicationStatus.pending_review,
        )
        .order_by(PartnerApplication.submitted_at.desc())
        .first()
    )
    if application:
        return "pending_review", application.business_name, False

    rejected = (
        db.query(PartnerApplication)
        .filter(
            PartnerApplication.user_id == user_id,
            PartnerApplication.status == PartnerApplicationStatus.rejected,
        )
        .order_by(PartnerApplication.submitted_at.desc())
        .first()
    )
    if rejected:
        return "rejected", rejected.business_name, False

    return "none", None, False


def _rider_state(db: Session, user_id: uuid.UUID) -> tuple[str, bool]:
    """Derive rider status from profile + application records."""
    profile = db.query(RiderProfile).filter(RiderProfile.user_id == user_id).first()
    if profile:
        # Suspended/deactivated riders still report approved; the app shows
        # account-specific messaging rather than re-applying.
        return "approved", profile.active_status and not profile.suspended

    pending = (
        db.query(RiderApplication)
        .filter(
            RiderApplication.user_id == user_id,
            RiderApplication.status == ApplicationStatus.pending_review,
        )
        .order_by(RiderApplication.submitted_at.desc())
        .first()
    )
    if pending:
        return "pending_review", False

    rejected = (
        db.query(RiderApplication)
        .filter(
            RiderApplication.user_id == user_id,
            RiderApplication.status == ApplicationStatus.rejected,
        )
        .order_by(RiderApplication.submitted_at.desc())
        .first()
    )
    if rejected:
        return "rejected", False

    return "none", False


@router.get("/me", response_model=MeOut)
def read_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    partner_status, business_name, is_active = _partner_state(db, current_user.id)
    rider_status, rider_active = _rider_state(db, current_user.id)
    return MeOut(
        id=current_user.id,
        name=current_user.name,
        phone=current_user.phone,
        role=current_user.role,
        partner_status=partner_status,
        partner_business_name=business_name,
        is_active_partner=is_active,
        rider_status=rider_status,
        is_active_rider=rider_active,
    )
