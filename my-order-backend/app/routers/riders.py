from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.dependencies import get_db, get_current_user, require_admin
from app.models.user import User, UserRole
from app.models.rider import RiderApplication, RiderProfile, ApplicationStatus
from app.schemas.rider import (
    RiderApplicationCreate,
    RiderApplicationOut,
    RiderReviewRequest,
    ActiveRiderOut,
    RiderSummaryOut,
)

router = APIRouter(prefix="/riders", tags=["Riders"])


@router.get("", response_model=list[RiderSummaryOut])
def list_riders(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Admin: list all riders (application + profile status)."""
    riders = db.query(User).filter(User.role == UserRole.rider).all()
    summaries = []
    for user in riders:
        profile = db.query(RiderProfile).filter(RiderProfile.user_id == user.id).first()
        if profile is None:
            continue
        summaries.append(RiderSummaryOut(
            user_id=user.id,
            name=user.name,
            phone=user.phone,
            application_status=profile.application_status,
            active_status=profile.active_status,
            suspended=profile.suspended,
        ))
    return summaries


@router.get("/active", response_model=list[ActiveRiderOut])
def list_active_riders(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Admin: assignable riders (approved profile, active, not suspended)."""
    profiles = (
        db.query(RiderProfile)
        .filter(
            RiderProfile.application_status == ApplicationStatus.approved,
            RiderProfile.active_status.is_(True),
            RiderProfile.suspended.is_(False),
        )
        .join(User, RiderProfile.user_id == User.id)
        .order_by(User.name)
        .all()
    )
    users = {u.id: u for u in db.query(User).filter(User.role == UserRole.rider).all()}
    return [
        ActiveRiderOut(user_id=p.user_id, name=users[p.user_id].name if p.user_id in users else "", phone=users[p.user_id].phone if p.user_id in users else "")
        for p in profiles
        if p.user_id in users
    ]


@router.get("/applications", response_model=list[RiderApplicationOut])
def list_applications(
    review_status: ApplicationStatus = Query(default=ApplicationStatus.pending_review, alias="status"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: list rider applications by status (default: pending review)."""
    return (
        db.query(RiderApplication)
        .filter(RiderApplication.status == review_status)
        .order_by(RiderApplication.submitted_at.desc())
        .all()
    )


@router.post("/apply", response_model=RiderApplicationOut, status_code=status.HTTP_201_CREATED)
def apply(payload: RiderApplicationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.rider:
        raise HTTPException(status_code=403, detail="Only rider accounts can submit a rider application")

    existing = db.query(RiderApplication).filter(
        RiderApplication.user_id == current_user.id,
        RiderApplication.status == ApplicationStatus.pending_review,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already have a pending application")

    application = RiderApplication(
        user_id=current_user.id,
        nrc=payload.nrc,
        license_number=payload.license_number,
        vehicle_plate=payload.vehicle_plate,
        photo_url=payload.photo_url,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application

@router.patch("/{application_id}/approve", response_model=RiderApplicationOut)
def approve(application_id: uuid.UUID, payload: RiderReviewRequest, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    application = db.query(RiderApplication).filter(RiderApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    application.status = ApplicationStatus.approved
    application.reviewer_notes = payload.reviewer_notes
    application.reviewed_at = datetime.utcnow()

    profile = RiderProfile(
        user_id=application.user_id,
        nrc=application.nrc,
        vehicle_plate=application.vehicle_plate,
        photo_url=application.photo_url,
        application_status=ApplicationStatus.approved,
        active_status=True,
    )
    db.add(profile)
    db.commit()
    db.refresh(application)
    return application

@router.patch("/{application_id}/reject", response_model=RiderApplicationOut)
def reject(application_id: uuid.UUID, payload: RiderReviewRequest, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    application = db.query(RiderApplication).filter(RiderApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    application.status = ApplicationStatus.rejected
    application.reviewer_notes = payload.reviewer_notes
    application.reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(application)
    return application
