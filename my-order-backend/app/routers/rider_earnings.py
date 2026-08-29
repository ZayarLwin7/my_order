import uuid
from datetime import datetime, time
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, require_admin
from app.models.rider import RiderProfile
from app.models.rider_earnings import (
    RiderCompensationRate,
    RiderEarning,
    RiderEarningStatus,
    RiderPayout,
    RiderPayoutStatus,
)
from app.models.user import User, UserRole
from app.schemas.rider_earnings import (
    RiderCompensationRateCreate,
    RiderCompensationRateOut,
    RiderEarningOut,
    RiderEarningsSummary,
    RiderPayoutCreate,
    RiderPayoutFailureRequest,
    RiderPayoutOut,
    RiderPayoutPaymentRequest,
)

router = APIRouter(prefix="/riders", tags=["Rider Earnings"])


def _summary(db: Session, rider_user_id: uuid.UUID) -> RiderEarningsSummary:
    def total_for(entry_status: RiderEarningStatus) -> Decimal:
        total = db.query(func.coalesce(func.sum(RiderEarning.amount), 0)).filter(
            RiderEarning.rider_user_id == rider_user_id,
            RiderEarning.status == entry_status,
        ).scalar()
        return Decimal(total or 0)

    return RiderEarningsSummary(
        available_amount=total_for(RiderEarningStatus.available),
        processing_amount=total_for(RiderEarningStatus.processing),
        paid_amount=total_for(RiderEarningStatus.paid),
    )


@router.post("/compensation-rates", response_model=RiderCompensationRateOut, status_code=status.HTTP_201_CREATED)
def create_compensation_rate(
    payload: RiderCompensationRateCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if db.query(RiderCompensationRate).filter(RiderCompensationRate.effective_from == payload.effective_from).first():
        raise HTTPException(status_code=400, detail="A rate already exists for this effective date")
    rate = RiderCompensationRate(created_by_user_id=admin.id, **payload.model_dump())
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate


@router.get("/compensation-rates", response_model=list[RiderCompensationRateOut])
def list_compensation_rates(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return db.query(RiderCompensationRate).order_by(RiderCompensationRate.effective_from.desc()).all()


@router.get("/me/earnings/summary", response_model=RiderEarningsSummary)
def my_earnings_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.rider:
        raise HTTPException(status_code=403, detail="Only rider accounts can view rider earnings")
    return _summary(db, current_user.id)


@router.get("/me/earnings", response_model=list[RiderEarningOut])
def my_earnings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.rider:
        raise HTTPException(status_code=403, detail="Only rider accounts can view rider earnings")
    return db.query(RiderEarning).filter(RiderEarning.rider_user_id == current_user.id).order_by(RiderEarning.created_at.desc()).all()


@router.get("/payouts/me", response_model=list[RiderPayoutOut])
def my_payouts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.rider:
        raise HTTPException(status_code=403, detail="Only rider accounts can view rider payouts")
    return db.query(RiderPayout).filter(RiderPayout.rider_user_id == current_user.id).order_by(RiderPayout.created_at.desc()).all()


@router.get("/{rider_user_id}/earnings/summary", response_model=RiderEarningsSummary)
def rider_earnings_summary(
    rider_user_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if not db.query(RiderProfile).filter(RiderProfile.user_id == rider_user_id).first():
        raise HTTPException(status_code=404, detail="Rider profile not found")
    return _summary(db, rider_user_id)


@router.get("/{rider_user_id}/earnings", response_model=list[RiderEarningOut])
def rider_earnings(
    rider_user_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return db.query(RiderEarning).filter(RiderEarning.rider_user_id == rider_user_id).order_by(RiderEarning.created_at.desc()).all()


@router.post("/payouts", response_model=RiderPayoutOut, status_code=status.HTTP_201_CREATED)
def create_payout(
    payload: RiderPayoutCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if payload.period_end < payload.period_start:
        raise HTTPException(status_code=400, detail="period_end must be on or after period_start")
    if not db.query(RiderProfile).filter(RiderProfile.user_id == payload.rider_user_id).first():
        raise HTTPException(status_code=404, detail="Rider profile not found")
    start = datetime.combine(payload.period_start, time.min)
    end = datetime.combine(payload.period_end, time.max)
    earnings = db.query(RiderEarning).filter(
        RiderEarning.rider_user_id == payload.rider_user_id,
        RiderEarning.status == RiderEarningStatus.available,
        RiderEarning.created_at >= start,
        RiderEarning.created_at <= end,
    ).with_for_update().all()
    per_way_amount = sum((earning.amount for earning in earnings), Decimal("0"))
    total_amount = payload.salary_amount + per_way_amount
    if total_amount <= 0:
        raise HTTPException(status_code=400, detail="Payout must include salary or completed-way earnings")

    payout = RiderPayout(
        rider_user_id=payload.rider_user_id,
        period_start=payload.period_start,
        period_end=payload.period_end,
        salary_amount=payload.salary_amount,
        per_way_amount=per_way_amount,
        total_amount=total_amount,
        note=payload.note,
    )
    db.add(payout)
    db.flush()
    for earning in earnings:
        earning.status = RiderEarningStatus.processing
        earning.payout_id = payout.id
    db.commit()
    db.refresh(payout)
    return payout


@router.patch("/payouts/{payout_id}/paid", response_model=RiderPayoutOut)
def mark_payout_paid(
    payout_id: uuid.UUID,
    payload: RiderPayoutPaymentRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    payout = db.query(RiderPayout).filter(RiderPayout.id == payout_id).with_for_update().first()
    if not payout:
        raise HTTPException(status_code=404, detail="Rider payout not found")
    if payout.status != RiderPayoutStatus.pending_payment:
        raise HTTPException(status_code=400, detail="Only pending payouts can be marked paid")
    if db.query(RiderPayout).filter(RiderPayout.payment_reference == payload.payment_reference).first():
        raise HTTPException(status_code=400, detail="Payment reference has already been used")
    payout.status = RiderPayoutStatus.paid
    payout.payment_reference = payload.payment_reference
    payout.note = payload.note or payout.note
    payout.paid_at = datetime.utcnow()
    db.query(RiderEarning).filter(
        RiderEarning.payout_id == payout.id,
        RiderEarning.status == RiderEarningStatus.processing,
    ).update({RiderEarning.status: RiderEarningStatus.paid}, synchronize_session=False)
    db.commit()
    db.refresh(payout)
    return payout


@router.patch("/payouts/{payout_id}/fail", response_model=RiderPayoutOut)
def fail_payout(
    payout_id: uuid.UUID,
    payload: RiderPayoutFailureRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    payout = db.query(RiderPayout).filter(RiderPayout.id == payout_id).with_for_update().first()
    if not payout:
        raise HTTPException(status_code=404, detail="Rider payout not found")
    if payout.status != RiderPayoutStatus.pending_payment:
        raise HTTPException(status_code=400, detail="Only pending payouts can be failed")
    payout.status = RiderPayoutStatus.failed
    payout.note = payload.note
    db.query(RiderEarning).filter(
        RiderEarning.payout_id == payout.id,
        RiderEarning.status == RiderEarningStatus.processing,
    ).update(
        {RiderEarning.status: RiderEarningStatus.available, RiderEarning.payout_id: None},
        synchronize_session=False,
    )
    db.commit()
    db.refresh(payout)
    return payout
