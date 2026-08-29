import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, require_admin
from app.models.user import User, UserRole
from app.models.order import Order, OrderStatus, OrderTrackingLog
from app.models.dispute import Dispute, DisputeStatus, ResolutionType
from app.models.rider import RiderProfile
from app.models.partner import (
    PartnerLedgerEntry,
    PartnerLedgerEntryStatus,
    PartnerLedgerEntryType,
    PlatformLedgerEntry,
    PlatformLedgerEntryType,
)
from app.models.wallet import WalletTransaction, TransactionType
from app.schemas.dispute import DisputeCreate, DisputeOut, DisputeResolveRequest
from app.config import settings

router = APIRouter(prefix="/disputes", tags=["Disputes"])

COMPLETION_STATUSES = {OrderStatus.delivered, OrderStatus.dropped_at_terminal}


@router.post("", response_model=DisputeOut, status_code=201)
def file_dispute(payload: DisputeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user.role != UserRole.sender or order.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the Sender who created this order can file a dispute")

    if order.status not in COMPLETION_STATUSES:
        raise HTTPException(status_code=400, detail="Only delivered or dropped-at-terminal orders can be disputed")

    # find when it was marked delivered/dropped, to enforce the 48-hour window (PRD 5.5)
    completion_log = (
        db.query(OrderTrackingLog)
        .filter(OrderTrackingLog.order_id == order.id, OrderTrackingLog.status == order.status)
        .order_by(OrderTrackingLog.created_at.desc())
        .first()
    )
    if completion_log:
        deadline = completion_log.created_at + timedelta(hours=settings.dispute_window_hours)
        if datetime.utcnow() > deadline:
            raise HTTPException(status_code=400, detail=f"Dispute window ({settings.dispute_window_hours}h) has passed")

    existing_open = db.query(Dispute).filter(Dispute.order_id == order.id, Dispute.status == DisputeStatus.open).first()
    if existing_open:
        raise HTTPException(status_code=400, detail="This order already has an open dispute")

    dispute = Dispute(
        order_id=order.id,
        filed_by_user_id=current_user.id,
        reason=payload.reason,
        description=payload.description,
        order_status_before_dispute=order.status,
    )
    order.status = OrderStatus.disputed
    partner_credit = db.query(PartnerLedgerEntry).filter(
        PartnerLedgerEntry.order_id == order.id,
        PartnerLedgerEntry.type == PartnerLedgerEntryType.cod_credit,
    ).first()
    if partner_credit and partner_credit.status == PartnerLedgerEntryStatus.available:
        partner_credit.status = PartnerLedgerEntryStatus.on_hold
        partner_credit.note = "On hold while dispute is open"
    db.add(OrderTrackingLog(order_id=order.id, status=OrderStatus.disputed, note=f"Dispute filed: {payload.reason.value}"))
    db.add(dispute)
    db.commit()
    db.refresh(dispute)
    return dispute


@router.get("/{dispute_id}", response_model=DisputeOut)
def get_dispute(dispute_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    if current_user.role != UserRole.admin and dispute.filed_by_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this dispute")

    return dispute


@router.patch("/{dispute_id}/resolve", response_model=DisputeOut)
def resolve_dispute(dispute_id: uuid.UUID, payload: DisputeResolveRequest, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    if dispute.status == DisputeStatus.resolved:
        raise HTTPException(status_code=400, detail="Dispute has already been resolved")

    order = db.query(Order).filter(Order.id == dispute.order_id).first()

    if payload.resolution_type in (ResolutionType.full_refund, ResolutionType.partial_refund):
        if payload.resolved_amount is None:
            raise HTTPException(status_code=400, detail="resolved_amount is required for a refund resolution")
        if payload.refund_payer is None:
            raise HTTPException(status_code=400, detail="refund_payer is required for a refund resolution")
        # PRD 5.4 refund cap: capped at declared item value, up to the platform max
        max_allowed = min(float(order.item_value), settings.refund_cap_mmk)
        if float(payload.resolved_amount) > max_allowed:
            raise HTTPException(
                status_code=400,
                detail=f"resolved_amount exceeds refund cap (max allowed: {max_allowed} MMK)",
            )

    if payload.resolution_type == ResolutionType.wallet_adjustment and order.rider_id:
        if payload.resolved_amount is None:
            raise HTTPException(status_code=400, detail="resolved_amount is required for a wallet adjustment")
        # resolved_amount is signed: positive = credit the rider (they were owed more),
        # negative = debit the rider (they were holding too much cash)
        rider_profile = db.query(RiderProfile).filter(RiderProfile.user_id == order.rider_id).first()
        if rider_profile:
            rider_profile.wallet_balance = (rider_profile.wallet_balance or 0) + payload.resolved_amount
            db.add(WalletTransaction(
                rider_user_id=order.rider_id,
                order_id=order.id,
                type=TransactionType.adjustment,
                amount=payload.resolved_amount,
                note=f"Dispute adjustment: {payload.reviewer_notes or dispute.reason.value}",
            ))

    partner_credit = db.query(PartnerLedgerEntry).filter(
        PartnerLedgerEntry.order_id == order.id,
        PartnerLedgerEntry.type == PartnerLedgerEntryType.cod_credit,
    ).first()
    if (
        payload.resolution_type in (ResolutionType.full_refund, ResolutionType.partial_refund)
        and payload.refund_payer is not None
        and payload.refund_payer.value == "partner"
        and not partner_credit
    ):
        raise HTTPException(status_code=400, detail="A partner-funded refund requires a COD partner order")
    if partner_credit:
        if partner_credit.status == PartnerLedgerEntryStatus.on_hold:
            partner_credit.note = "Dispute resolved; awaiting remittance allocation and dispute-window expiry"
        if payload.resolution_type in (ResolutionType.full_refund, ResolutionType.partial_refund) and payload.refund_payer.value == "partner":
            # A refund reduces the amount payable to the partner.  Keep it as a
            # separate signed entry so the original COD collection is immutable.
            # If the original credit is already paid/processing, this becomes a
            # recovery against the partner's next settlement.
            db.add(PartnerLedgerEntry(
                partner_user_id=partner_credit.partner_user_id,
                order_id=order.id,
                type=PartnerLedgerEntryType.refund_adjustment,
                amount=-(payload.resolved_amount or 0),
                status=partner_credit.status,
                available_at=partner_credit.available_at,
                note=f"Dispute refund: {payload.resolution_type.value}",
            ))

    if payload.resolution_type in (ResolutionType.full_refund, ResolutionType.partial_refund):
        if payload.refund_payer.value == "platform":
            db.add(PlatformLedgerEntry(
                order_id=order.id,
                partner_user_id=order.sender_id if order.cod_amount > 0 else None,
                type=PlatformLedgerEntryType.customer_refund,
                amount=-(payload.resolved_amount or 0),
                note=f"Platform-funded dispute refund: {dispute.id}",
            ))
        elif payload.refund_payer.value == "rider":
            rider_profile = db.query(RiderProfile).filter(RiderProfile.user_id == order.rider_id).first() if order.rider_id else None
            if not rider_profile:
                raise HTTPException(status_code=400, detail="A rider-funded refund requires an assigned rider profile")
            rider_profile.wallet_balance = (rider_profile.wallet_balance or 0) - payload.resolved_amount
            db.add(WalletTransaction(
                rider_user_id=order.rider_id,
                order_id=order.id,
                type=TransactionType.adjustment,
                amount=-payload.resolved_amount,
                note=f"Rider-funded dispute refund: {dispute.id}",
            ))
            db.add(PlatformLedgerEntry(
                order_id=order.id,
                rider_user_id=order.rider_id,
                type=PlatformLedgerEntryType.rider_refund_recovery,
                amount=payload.resolved_amount,
                note=f"Rider-funded dispute refund: {dispute.id}",
            ))
            db.add(PlatformLedgerEntry(
                order_id=order.id,
                rider_user_id=order.rider_id,
                type=PlatformLedgerEntryType.customer_refund,
                amount=-payload.resolved_amount,
                note=f"Customer refund funded by rider: {dispute.id}",
            ))

    dispute.status = DisputeStatus.resolved
    dispute.resolution_type = payload.resolution_type
    dispute.resolved_amount = payload.resolved_amount
    dispute.refund_payer = payload.refund_payer
    dispute.reviewer_notes = payload.reviewer_notes
    dispute.resolved_at = datetime.utcnow()

    # order goes back to its pre-dispute completed status so it re-enters settlement (PRD 5.5)
    order.status = dispute.order_status_before_dispute
    db.add(OrderTrackingLog(
        order_id=order.id,
        status=order.status,
        note=f"Dispute resolved: {payload.resolution_type.value}",
    ))

    db.commit()
    db.refresh(dispute)
    return dispute
