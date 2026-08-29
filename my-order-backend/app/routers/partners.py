import uuid
from datetime import datetime, time
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, require_admin
from app.models.dispute import Dispute, DisputeStatus
from app.models.partner import (
    PartnerApplication,
    PartnerApplicationStatus,
    PartnerLedgerEntry,
    PartnerLedgerEntryStatus,
    PartnerProfile,
    PartnerSettlement,
    PartnerSettlementStatus,
    PlatformLedgerEntry,
    PlatformLedgerEntryType,
)
from app.models.user import User, UserRole
from app.models.wallet import RiderRemittanceAllocation
from app.schemas.partner import (
    PartnerApplicationCreate,
    PartnerApplicationOut,
    PartnerLedgerEntryOut,
    PartnerReviewRequest,
    PartnerSettlementCreate,
    PartnerSettlementFailureRequest,
    PartnerSettlementOut,
    PartnerSettlementPaymentRequest,
    PartnerSettlementSummary,
    PartnerPayoutMethodRequest,
    PartnerSuspendRequest,
)

router = APIRouter(prefix="/partners", tags=["Partner Senders"])


def _settlement_summary(db: Session, partner_user_id: uuid.UUID) -> PartnerSettlementSummary:
    def total_for(status: PartnerLedgerEntryStatus) -> Decimal:
        total = (
            db.query(func.coalesce(func.sum(PartnerLedgerEntry.amount), 0))
            .filter(
                PartnerLedgerEntry.partner_user_id == partner_user_id,
                PartnerLedgerEntry.status == status,
            )
            .scalar()
        )
        return Decimal(total or 0)

    return PartnerSettlementSummary(
        available_amount=total_for(PartnerLedgerEntryStatus.available),
        on_hold_amount=total_for(PartnerLedgerEntryStatus.on_hold),
        processing_amount=total_for(PartnerLedgerEntryStatus.processing),
        paid_amount=total_for(PartnerLedgerEntryStatus.paid),
    )


@router.post("/apply", response_model=PartnerApplicationOut, status_code=status.HTTP_201_CREATED)
def apply(
    payload: PartnerApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.sender:
        raise HTTPException(status_code=403, detail="Only Sender accounts can apply as partner senders")

    if db.query(PartnerProfile).filter(PartnerProfile.user_id == current_user.id).first():
        raise HTTPException(status_code=400, detail="This sender is already an approved partner")

    if db.query(PartnerApplication).filter(
        PartnerApplication.user_id == current_user.id,
        PartnerApplication.status == PartnerApplicationStatus.pending_review,
    ).first():
        raise HTTPException(status_code=400, detail="You already have a pending partner application")

    application = PartnerApplication(user_id=current_user.id, **payload.model_dump())
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.get("/applications", response_model=list[PartnerApplicationOut])
def list_applications(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return db.query(PartnerApplication).order_by(PartnerApplication.submitted_at.desc()).all()


@router.patch("/{application_id}/approve", response_model=PartnerApplicationOut)
def approve(
    application_id: uuid.UUID,
    payload: PartnerReviewRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    application = db.query(PartnerApplication).filter(PartnerApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Partner application not found")
    if application.status != PartnerApplicationStatus.pending_review:
        raise HTTPException(status_code=400, detail="Only pending applications can be approved")

    application.status = PartnerApplicationStatus.approved
    application.reviewer_notes = payload.reviewer_notes
    application.reviewed_at = datetime.utcnow()
    db.add(PartnerProfile(
        user_id=application.user_id,
        business_name=application.business_name,
        business_address=application.business_address,
        contact_phone=application.contact_phone,
    ))
    db.commit()
    db.refresh(application)
    return application


@router.patch("/{application_id}/reject", response_model=PartnerApplicationOut)
def reject(
    application_id: uuid.UUID,
    payload: PartnerReviewRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    application = db.query(PartnerApplication).filter(PartnerApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Partner application not found")
    if application.status != PartnerApplicationStatus.pending_review:
        raise HTTPException(status_code=400, detail="Only pending applications can be rejected")

    application.status = PartnerApplicationStatus.rejected
    application.reviewer_notes = payload.reviewer_notes
    application.reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(application)
    return application


@router.get("/{partner_user_id}/ledger", response_model=list[PartnerLedgerEntryOut])
def get_ledger(
    partner_user_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if not db.query(PartnerProfile).filter(PartnerProfile.user_id == partner_user_id).first():
        raise HTTPException(status_code=404, detail="Partner profile not found")
    return (
        db.query(PartnerLedgerEntry)
        .filter(PartnerLedgerEntry.partner_user_id == partner_user_id)
        .order_by(PartnerLedgerEntry.created_at.desc())
        .all()
    )


@router.get("/{partner_user_id}/settlement-summary", response_model=PartnerSettlementSummary)
def get_settlement_summary(
    partner_user_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if not db.query(PartnerProfile).filter(PartnerProfile.user_id == partner_user_id).first():
        raise HTTPException(status_code=404, detail="Partner profile not found")
    return _settlement_summary(db, partner_user_id)


@router.get("/{partner_user_id}/settlements", response_model=list[PartnerSettlementOut])
def list_partner_settlements(
    partner_user_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if not db.query(PartnerProfile).filter(PartnerProfile.user_id == partner_user_id).first():
        raise HTTPException(status_code=404, detail="Partner profile not found")
    return (
        db.query(PartnerSettlement)
        .filter(PartnerSettlement.partner_user_id == partner_user_id)
        .order_by(PartnerSettlement.created_at.desc())
        .all()
    )


@router.get("/settlements/me/summary", response_model=PartnerSettlementSummary)
def get_my_settlement_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not db.query(PartnerProfile).filter(PartnerProfile.user_id == current_user.id).first():
        raise HTTPException(status_code=404, detail="Approved partner profile not found")
    return _settlement_summary(db, current_user.id)


@router.get("/settlements/me", response_model=list[PartnerSettlementOut])
def list_my_settlements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not db.query(PartnerProfile).filter(PartnerProfile.user_id == current_user.id).first():
        raise HTTPException(status_code=404, detail="Approved partner profile not found")
    return (
        db.query(PartnerSettlement)
        .filter(PartnerSettlement.partner_user_id == current_user.id)
        .order_by(PartnerSettlement.created_at.desc())
        .all()
    )


@router.post("/ledger/release", response_model=dict[str, int])
def release_matured_cod(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Release COD credits only after their dispute window has expired."""
    entries = db.query(PartnerLedgerEntry).filter(
        PartnerLedgerEntry.status == PartnerLedgerEntryStatus.on_hold,
        PartnerLedgerEntry.available_at <= datetime.utcnow(),
        ~db.query(Dispute).filter(
            Dispute.order_id == PartnerLedgerEntry.order_id,
            Dispute.status == DisputeStatus.open,
        ).exists(),
    ).with_for_update().all()
    released = 0
    for entry in entries:
        remitted_cod = db.query(func.coalesce(func.sum(RiderRemittanceAllocation.cod_amount), 0)).filter(
            RiderRemittanceAllocation.order_id == entry.order_id,
        ).scalar()
        if remitted_cod >= entry.amount:
            entry.status = PartnerLedgerEntryStatus.available
            entry.note = "COD fully remitted and dispute window has expired"
            released += 1
    db.commit()
    return {"released_entries": released}


@router.patch("/me/payout-method", status_code=status.HTTP_204_NO_CONTENT)
def set_payout_method(
    payload: PartnerPayoutMethodRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Approved partner profile not found")
    profile.mmqr_account_name = payload.mmqr_account_name
    profile.mmqr_account_reference = payload.mmqr_account_reference
    # Any change must be reverified before a payout can be created.
    profile.payout_verified_at = None
    profile.payout_verified_by_user_id = None
    db.commit()


@router.patch("/{partner_user_id}/payout-method/verify", status_code=status.HTTP_204_NO_CONTENT)
def verify_payout_method(
    partner_user_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == partner_user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Partner profile not found")
    if not profile.mmqr_account_name or not profile.mmqr_account_reference:
        raise HTTPException(status_code=400, detail="Partner has not provided an MMQR payout method")
    profile.payout_verified_at = datetime.utcnow()
    profile.payout_verified_by_user_id = admin.id
    db.commit()


@router.patch("/{partner_user_id}/suspend", status_code=status.HTTP_204_NO_CONTENT)
def suspend_partner(
    partner_user_id: uuid.UUID,
    payload: PartnerSuspendRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == partner_user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Partner profile not found")
    profile.suspended = payload.suspended
    profile.active_status = not payload.suspended
    db.commit()


@router.post("/settlements", response_model=PartnerSettlementOut, status_code=status.HTTP_201_CREATED)
def create_settlement(
    payload: PartnerSettlementCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if payload.period_end < payload.period_start:
        raise HTTPException(status_code=400, detail="period_end must be on or after period_start")
    profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == payload.partner_user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Partner profile not found")
    if not profile.payout_verified_at:
        raise HTTPException(status_code=400, detail="Partner MMQR payout method must be verified before settlement")

    start = datetime.combine(payload.period_start, time.min)
    end = datetime.combine(payload.period_end, time.max)
    entries = (
        db.query(PartnerLedgerEntry)
        .filter(
            PartnerLedgerEntry.partner_user_id == payload.partner_user_id,
            PartnerLedgerEntry.status == PartnerLedgerEntryStatus.available,
            or_(
                and_(PartnerLedgerEntry.created_at >= start, PartnerLedgerEntry.created_at <= end),
                and_(PartnerLedgerEntry.available_at >= start, PartnerLedgerEntry.available_at <= end),
            ),
        )
        .with_for_update()
        .all()
    )
    total = sum((entry.amount for entry in entries), Decimal("0"))
    if total <= 0:
        raise HTTPException(status_code=400, detail="No positive available balance exists for this settlement period")

    settlement = PartnerSettlement(
        partner_user_id=payload.partner_user_id,
        period_start=payload.period_start,
        period_end=payload.period_end,
        total_amount=total,
        note=payload.note,
    )
    db.add(settlement)
    db.flush()
    for entry in entries:
        entry.status = PartnerLedgerEntryStatus.processing
        entry.settlement_id = settlement.id
    db.commit()
    db.refresh(settlement)
    return settlement


@router.get("/settlements/{settlement_id}", response_model=PartnerSettlementOut)
def get_settlement(
    settlement_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    settlement = db.query(PartnerSettlement).filter(PartnerSettlement.id == settlement_id).with_for_update().first()
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    return settlement


@router.patch("/settlements/{settlement_id}/paid", response_model=PartnerSettlementOut)
def mark_settlement_paid(
    settlement_id: uuid.UUID,
    payload: PartnerSettlementPaymentRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    settlement = db.query(PartnerSettlement).filter(PartnerSettlement.id == settlement_id).with_for_update().first()
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    if settlement.status != PartnerSettlementStatus.pending_payment:
        raise HTTPException(status_code=400, detail="Only pending settlements can be marked paid")
    if db.query(PartnerSettlement).filter(
        PartnerSettlement.mmqr_reference == payload.mmqr_reference,
        PartnerSettlement.id != settlement.id,
    ).first():
        raise HTTPException(status_code=400, detail="MMQR reference has already been used")

    settlement.status = PartnerSettlementStatus.paid
    settlement.mmqr_reference = payload.mmqr_reference
    settlement.note = payload.note or settlement.note
    settlement.paid_at = datetime.utcnow()
    db.query(PartnerLedgerEntry).filter(
        PartnerLedgerEntry.settlement_id == settlement.id,
        PartnerLedgerEntry.status == PartnerLedgerEntryStatus.processing,
    ).update({PartnerLedgerEntry.status: PartnerLedgerEntryStatus.paid}, synchronize_session=False)
    db.add(PlatformLedgerEntry(
        partner_user_id=settlement.partner_user_id,
        settlement_id=settlement.id,
        type=PlatformLedgerEntryType.partner_payout,
        amount=-settlement.total_amount,
        note=f"MMQR partner payout: {payload.mmqr_reference}",
    ))
    db.commit()
    db.refresh(settlement)
    return settlement


@router.patch("/settlements/{settlement_id}/fail", response_model=PartnerSettlementOut)
def fail_settlement(
    settlement_id: uuid.UUID,
    payload: PartnerSettlementFailureRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    settlement = db.query(PartnerSettlement).filter(PartnerSettlement.id == settlement_id).first()
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    if settlement.status != PartnerSettlementStatus.pending_payment:
        raise HTTPException(status_code=400, detail="Only pending settlements can be failed")

    settlement.status = PartnerSettlementStatus.failed
    settlement.note = payload.note
    db.query(PartnerLedgerEntry).filter(
        PartnerLedgerEntry.settlement_id == settlement.id,
        PartnerLedgerEntry.status == PartnerLedgerEntryStatus.processing,
    ).update(
        {
            PartnerLedgerEntry.status: PartnerLedgerEntryStatus.available,
            PartnerLedgerEntry.settlement_id: None,
        },
        synchronize_session=False,
    )
    db.commit()
    db.refresh(settlement)
    return settlement
