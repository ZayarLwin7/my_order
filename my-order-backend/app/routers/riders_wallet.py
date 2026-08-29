import uuid
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_admin
from app.models.user import User
from app.models.rider import RiderProfile
from app.models.order import Order, OrderStatus
from app.models.wallet import RiderRemittanceAllocation, WalletTransaction, TransactionType
from app.models.partner import PlatformLedgerEntry, PlatformLedgerEntryType
from app.schemas.wallet import (
    RemittanceAllocationOut,
    RemittanceAllocationRequest,
    RemittanceRequest,
    SuspendRequest,
    WalletOut,
    WalletTransactionOut,
)
from app.config import settings

router = APIRouter(prefix="/riders", tags=["Rider Wallet"])


@router.get("/{rider_user_id}/wallet", response_model=WalletOut)
def get_wallet(rider_user_id: uuid.UUID, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    profile = db.query(RiderProfile).filter(RiderProfile.user_id == rider_user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Rider profile not found")

    return WalletOut(
        rider_user_id=rider_user_id,
        wallet_balance=profile.wallet_balance,
        active_status=profile.active_status,
        suspended=profile.suspended,
        alert=float(profile.wallet_balance) >= settings.wallet_alert_threshold,
    )


@router.get("/{rider_user_id}/wallet/transactions", response_model=list[WalletTransactionOut])
def get_wallet_transactions(rider_user_id: uuid.UUID, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    profile = db.query(RiderProfile).filter(RiderProfile.user_id == rider_user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Rider profile not found")

    return (
        db.query(WalletTransaction)
        .filter(WalletTransaction.rider_user_id == rider_user_id)
        .order_by(WalletTransaction.created_at.desc())
        .all()
    )


@router.patch("/{rider_user_id}/suspend", response_model=WalletOut)
def suspend_rider(rider_user_id: uuid.UUID, payload: SuspendRequest, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    profile = db.query(RiderProfile).filter(RiderProfile.user_id == rider_user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Rider profile not found")

    profile.suspended = payload.suspended
    if payload.suspended:
        profile.active_status = False  # no new assignments while suspended (PRD 5.6)
    else:
        profile.active_status = True  # lifting suspension restores assignment eligibility

    db.commit()
    db.refresh(profile)

    return WalletOut(
        rider_user_id=rider_user_id,
        wallet_balance=profile.wallet_balance,
        active_status=profile.active_status,
        suspended=profile.suspended,
        alert=float(profile.wallet_balance) >= settings.wallet_alert_threshold,
    )


@router.post("/{rider_user_id}/wallet/remittances", response_model=WalletOut)
def record_remittance(
    rider_user_id: uuid.UUID,
    payload: RemittanceRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Remittance amount must be positive")
    profile = db.query(RiderProfile).filter(RiderProfile.user_id == rider_user_id).with_for_update().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Rider profile not found")
    wallet_balance = profile.wallet_balance or 0
    if payload.amount > wallet_balance:
        raise HTTPException(status_code=400, detail="Remittance cannot exceed the rider wallet balance")
    if db.query(WalletTransaction).filter(WalletTransaction.reference == payload.reference).first():
        raise HTTPException(status_code=400, detail="Remittance reference has already been recorded")

    profile.wallet_balance = wallet_balance - payload.amount
    db.add(WalletTransaction(
        rider_user_id=rider_user_id,
        type=TransactionType.remittance,
        amount=-payload.amount,
        reference=payload.reference,
        note=f"Remittance {payload.reference}: {payload.note or ''}".strip(),
    ))
    db.add(PlatformLedgerEntry(
        rider_user_id=rider_user_id,
        type=PlatformLedgerEntryType.rider_remittance,
        amount=payload.amount,
        note=f"Rider remittance {payload.reference}: {payload.note or ''}".strip(),
    ))
    db.commit()
    db.refresh(profile)
    return WalletOut(
        rider_user_id=rider_user_id,
        wallet_balance=profile.wallet_balance,
        active_status=profile.active_status,
        suspended=profile.suspended,
        alert=float(profile.wallet_balance) >= settings.wallet_alert_threshold,
    )


@router.post("/{rider_user_id}/wallet/remittances/{remittance_transaction_id}/allocations", response_model=list[RemittanceAllocationOut])
def allocate_remittance(
    rider_user_id: uuid.UUID,
    remittance_transaction_id: uuid.UUID,
    payload: RemittanceAllocationRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    remittance = db.query(WalletTransaction).filter(
        WalletTransaction.id == remittance_transaction_id,
        WalletTransaction.rider_user_id == rider_user_id,
        WalletTransaction.type == TransactionType.remittance,
    ).with_for_update().first()
    if not remittance:
        raise HTTPException(status_code=404, detail="Rider remittance transaction not found")

    requested: dict[uuid.UUID, tuple[Decimal, Decimal]] = {}
    for item in payload.allocations:
        if item.cod_amount + item.delivery_fee_amount <= 0:
            raise HTTPException(status_code=400, detail="Each allocation must include a COD or delivery-fee amount")
        cod, fee = requested.get(item.order_id, (0, 0))
        requested[item.order_id] = (cod + item.cod_amount, fee + item.delivery_fee_amount)

    existing_remittance_total = db.query(
        func.coalesce(func.sum(RiderRemittanceAllocation.cod_amount + RiderRemittanceAllocation.delivery_fee_amount), 0)
    ).filter(RiderRemittanceAllocation.remittance_transaction_id == remittance.id).scalar()
    requested_total = sum((cod + fee for cod, fee in requested.values()), 0)
    if existing_remittance_total + requested_total > -remittance.amount:
        raise HTTPException(status_code=400, detail="Allocations exceed the remitted amount")

    created = []
    for order_id, (cod_amount, fee_amount) in requested.items():
        order = db.query(Order).filter(Order.id == order_id).with_for_update().first()
        if not order or order.rider_id != rider_user_id:
            raise HTTPException(status_code=400, detail="Allocation order must belong to this rider")
        if order.status not in {OrderStatus.delivered, OrderStatus.dropped_at_terminal, OrderStatus.disputed}:
            raise HTTPException(status_code=400, detail="Only completed or disputed orders can be allocated")

        collection = db.query(WalletTransaction).filter(
            WalletTransaction.order_id == order.id,
            WalletTransaction.rider_user_id == rider_user_id,
            WalletTransaction.type == TransactionType.collection,
        ).first()
        if not collection:
            raise HTTPException(status_code=400, detail="No rider collection exists for this order")
        max_fee = order.delivery_fee if order.fee_payer.value == "recipient" else 0
        allocated_cod = db.query(func.coalesce(func.sum(RiderRemittanceAllocation.cod_amount), 0)).filter(
            RiderRemittanceAllocation.order_id == order.id,
        ).scalar()
        allocated_fee = db.query(func.coalesce(func.sum(RiderRemittanceAllocation.delivery_fee_amount), 0)).filter(
            RiderRemittanceAllocation.order_id == order.id,
        ).scalar()
        if allocated_cod + cod_amount > order.cod_amount or allocated_fee + fee_amount > max_fee:
            raise HTTPException(status_code=400, detail="Allocation exceeds cash collected for an order")

        allocation = RiderRemittanceAllocation(
            remittance_transaction_id=remittance.id,
            order_id=order.id,
            cod_amount=cod_amount,
            delivery_fee_amount=fee_amount,
            allocated_by_user_id=admin.id,
        )
        db.add(allocation)
        created.append(allocation)

    db.commit()
    for allocation in created:
        db.refresh(allocation)
    return created


@router.get("/{rider_user_id}/wallet/remittances/{remittance_transaction_id}/allocations", response_model=list[RemittanceAllocationOut])
def list_remittance_allocations(
    rider_user_id: uuid.UUID,
    remittance_transaction_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    remittance = db.query(WalletTransaction).filter(
        WalletTransaction.id == remittance_transaction_id,
        WalletTransaction.rider_user_id == rider_user_id,
        WalletTransaction.type == TransactionType.remittance,
    ).first()
    if not remittance:
        raise HTTPException(status_code=404, detail="Rider remittance transaction not found")
    return db.query(RiderRemittanceAllocation).filter(
        RiderRemittanceAllocation.remittance_transaction_id == remittance.id,
    ).order_by(RiderRemittanceAllocation.created_at).all()
