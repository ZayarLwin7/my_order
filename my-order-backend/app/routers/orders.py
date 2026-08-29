import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user, require_admin
from app.models.user import User, UserRole
from app.models.order import DeliveryMode, FeePayer, Order, OrderStatus, OrderTrackingLog
from app.models.pricing import DeliveryQuote, ItemSizeRate
from app.models.rider import RiderProfile, ApplicationStatus
from app.models.wallet import WalletTransaction, TransactionType
from app.models.partner import (
    PartnerLedgerEntry,
    PartnerLedgerEntryStatus,
    PartnerLedgerEntryType,
    PartnerProfile,
    PlatformLedgerEntry,
    PlatformLedgerEntryType,
)
from app.models.rider_earnings import RiderCompensationRate, RiderEarning
from app.config import settings
from app.schemas.order import (
    OrderCreate, OrderOut, OrderAssignRequest,
    OrderStatusUpdateRequest, OrderCancelRequest, OrderItemSizeVerifyRequest, OrderAdminFeeApprovalRequest,
    WalkinOrderCreate,
)

router = APIRouter(prefix="/orders", tags=["Orders"])

# valid forward transitions for PATCH /orders/{id}/status
ALLOWED_TRANSITIONS = {
    OrderStatus.assigned: {OrderStatus.picked_up},
    OrderStatus.picked_up: {OrderStatus.delivered, OrderStatus.dropped_at_terminal, OrderStatus.delivery_failed},
    OrderStatus.delivered: {OrderStatus.disputed},
    OrderStatus.dropped_at_terminal: {OrderStatus.disputed},
    OrderStatus.delivery_failed: {OrderStatus.returned, OrderStatus.cancelled_post_pickup, OrderStatus.disputed},
}


def _log(db: Session, order_id, status: OrderStatus, note: str | None = None):
    db.add(OrderTrackingLog(order_id=order_id, status=status, note=note))


@router.post("", response_model=OrderOut, status_code=http_status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.sender:
        raise HTTPException(status_code=403, detail="Only Sender accounts can create orders")
    if not payload.terms_accepted:
        raise HTTPException(status_code=400, detail="terms_accepted must be true to create an order")

    partner_profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == current_user.id).first()
    if payload.cod_amount > 0 and (
        not partner_profile or not partner_profile.active_status or partner_profile.suspended
    ):
        raise HTTPException(
            status_code=403,
            detail="COD orders are available only to active, approved partner senders",
        )

    quote = db.query(DeliveryQuote).filter(
        DeliveryQuote.id == payload.quote_id,
        DeliveryQuote.sender_id == current_user.id,
    ).with_for_update().first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.order_id is not None:
        raise HTTPException(status_code=400, detail="Quote has already been used")
    if quote.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Quote has expired; request a new quote")
    if payload.authorized_max_fee_mmk < quote.estimated_fee_mmk or payload.authorized_max_fee_mmk > quote.maximum_fee_mmk:
        raise HTTPException(
            status_code=400,
            detail=f"authorized_max_fee_mmk must be between {quote.estimated_fee_mmk} and {quote.maximum_fee_mmk}",
        )

    order = Order(
        sender_id=current_user.id,
        quote_id=quote.id,
        delivery_mode=DeliveryMode(quote.delivery_mode),
        recipient_name=payload.recipient_name,
        recipient_phone=payload.recipient_phone,
        pickup_address=payload.pickup_address,
        pickup_lat=payload.pickup_lat,
        pickup_lng=payload.pickup_lng,
        dropoff_address=quote.dropoff_address,
        dropoff_lat=quote.dropoff_lat,
        dropoff_lng=quote.dropoff_lng,
        terminal_name=quote.terminal_name,
        bus_line=quote.bus_line,
        item_size=None,
        item_value=payload.item_value,
        cod_amount=payload.cod_amount,
        delivery_fee=quote.estimated_fee_mmk,
        authorized_max_fee_mmk=payload.authorized_max_fee_mmk,
        fee_payer=FeePayer(quote.fee_payer),
        terms_accepted=payload.terms_accepted,
        status=OrderStatus.pending,
    )
    db.add(order)
    db.flush()  # get order.id before commit
    quote.order_id = order.id
    _log(db, order.id, OrderStatus.pending, "Order created")
    db.commit()
    db.refresh(order)
    return order


@router.post("/walkin", response_model=OrderOut, status_code=http_status.HTTP_201_CREATED)
def create_walkin_order(payload: WalkinOrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Staff creates an order on behalf of a walk-in customer who doesn't have an account."""
    if current_user.role != UserRole.staff:
        raise HTTPException(status_code=403, detail="Only Staff accounts can create walk-in orders")
    if not payload.terms_accepted:
        raise HTTPException(status_code=400, detail="terms_accepted must be true to create an order")

    # Walk-in orders do NOT support COD (cash transactions only at office)
    if payload.cod_amount > 0:
        raise HTTPException(
            status_code=400,
            detail="COD is not available for walk-in orders. Walk-in customers must pay at the office.",
        )

    quote = db.query(DeliveryQuote).filter(
        DeliveryQuote.id == payload.quote_id,
    ).with_for_update().first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.order_id is not None:
        raise HTTPException(status_code=400, detail="Quote has already been used")
    if quote.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Quote has expired; request a new quote")
    if payload.authorized_max_fee_mmk < quote.estimated_fee_mmk or payload.authorized_max_fee_mmk > quote.maximum_fee_mmk:
        raise HTTPException(
            status_code=400,
            detail=f"authorized_max_fee_mmk must be between {quote.estimated_fee_mmk} and {quote.maximum_fee_mmk}",
        )

    order = Order(
        sender_id=current_user.id,  # Staff member's ID (for system tracking)
        created_by_staff_id=current_user.id,  # Explicitly mark who created it
        is_walkin=True,
        walkin_sender_name=payload.walkin_sender_name,
        walkin_sender_phone=payload.walkin_sender_phone,
        quote_id=quote.id,
        delivery_mode=DeliveryMode(quote.delivery_mode),
        recipient_name=payload.recipient_name,
        recipient_phone=payload.recipient_phone,
        pickup_address=payload.pickup_address,
        pickup_lat=payload.pickup_lat,
        pickup_lng=payload.pickup_lng,
        dropoff_address=quote.dropoff_address,
        dropoff_lat=quote.dropoff_lat,
        dropoff_lng=quote.dropoff_lng,
        terminal_name=quote.terminal_name,
        bus_line=quote.bus_line,
        item_size=None,
        item_value=payload.item_value,
        cod_amount=0,  # No COD for walk-ins
        delivery_fee=quote.estimated_fee_mmk,
        authorized_max_fee_mmk=payload.authorized_max_fee_mmk,
        fee_payer=FeePayer(quote.fee_payer),
        terms_accepted=payload.terms_accepted,
        status=OrderStatus.pending,
    )
    db.add(order)
    db.flush()  # get order.id before commit
    quote.order_id = order.id
    _log(db, order.id, OrderStatus.pending, f"Walk-in order created by staff {current_user.id} for customer {payload.walkin_sender_name}")
    db.commit()
    db.refresh(order)
    return order


@router.patch("/{order_id}/verify-item-size", response_model=OrderOut)
def verify_item_size(
    order_id: uuid.UUID,
    payload: OrderItemSizeVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).with_for_update().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if current_user.role != UserRole.rider or order.rider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the assigned rider can verify item size")
    if order.status != OrderStatus.assigned:
        raise HTTPException(status_code=400, detail="Item size must be verified before pickup")
    if order.item_size:
        raise HTTPException(status_code=400, detail="Item size has already been verified")
    quote = db.query(DeliveryQuote).filter(DeliveryQuote.id == order.quote_id).with_for_update().first()
    rate = db.query(ItemSizeRate).filter(ItemSizeRate.name.ilike(payload.item_size.strip()), ItemSizeRate.active.is_(True)).first()
    if not quote or not rate:
        raise HTTPException(status_code=400, detail="An active item-size rate is required")

    final_fee = max(0, quote.estimated_fee_mmk + rate.surcharge_mmk)
    order.item_size = rate.name
    order.delivery_fee = final_fee
    order.price_confirmed_at = datetime.utcnow() if final_fee <= order.authorized_max_fee_mmk else None
    quote.final_item_size = rate.name
    quote.final_item_size_surcharge_mmk = rate.surcharge_mmk
    quote.final_fee_mmk = final_fee
    _log(db, order.id, order.status, f"Rider verified item size: {rate.name}; final fee {final_fee} MMK")
    db.commit()
    db.refresh(order)
    return order


@router.patch("/{order_id}/confirm-final-fee", response_model=OrderOut)
def confirm_final_fee(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).with_for_update().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if current_user.role != UserRole.sender or order.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the order sender can confirm the final fee")
    if order.status != OrderStatus.assigned or not order.item_size:
        raise HTTPException(status_code=400, detail="A rider must verify item size before fee confirmation")
    if order.price_confirmed_at:
        raise HTTPException(status_code=400, detail="Final fee is already approved")
    order.price_confirmed_at = datetime.utcnow()
    _log(db, order.id, order.status, f"Final delivery fee confirmed: {order.delivery_fee} MMK")
    db.commit()
    db.refresh(order)
    return order


@router.patch("/{order_id}/approve-final-fee", response_model=OrderOut)
def approve_final_fee(
    order_id: uuid.UUID,
    payload: OrderAdminFeeApprovalRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    order = db.query(Order).filter(Order.id == order_id).with_for_update().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatus.assigned or not order.item_size:
        raise HTTPException(status_code=400, detail="A rider must verify item size before admin approval")
    if order.price_confirmed_at:
        raise HTTPException(status_code=400, detail="Final fee is already approved")
    order.price_confirmed_at = datetime.utcnow()
    order.price_approved_by_admin_id = admin.id
    order.price_approval_note = payload.reason
    _log(db, order.id, order.status, f"Admin {admin.id} approved final fee {order.delivery_fee} MMK: {payload.reason}")
    db.commit()
    db.refresh(order)
    return order


@router.get("", response_model=list[OrderOut])
def list_orders(
    order_status: OrderStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: list orders, optionally filtered by status (e.g. pending queue)."""
    query = db.query(Order).order_by(Order.created_at.desc())
    if order_status is not None:
        query = query.filter(Order.status == order_status)
    return query.limit(100).all()


@router.patch("/{order_id}/assign", response_model=OrderOut)
def assign_order(order_id: uuid.UUID, payload: OrderAssignRequest, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    order = db.query(Order).filter(Order.id == order_id).with_for_update().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatus.pending:
        raise HTTPException(status_code=400, detail=f"Cannot assign an order in status '{order.status.value}'")

    rider_profile = db.query(RiderProfile).filter(RiderProfile.user_id == payload.rider_id).first()
    if not rider_profile:
        raise HTTPException(status_code=404, detail="Rider profile not found")
    if rider_profile.suspended:
        raise HTTPException(status_code=400, detail="Rider is currently suspended (wallet not reconciled)")
    if rider_profile.application_status != ApplicationStatus.approved or not rider_profile.active_status:
        raise HTTPException(status_code=400, detail="Rider is not an approved, active rider")

    order.rider_id = payload.rider_id
    order.status = OrderStatus.assigned
    _log(db, order.id, OrderStatus.assigned, f"Assigned by admin {admin.id}")
    db.commit()
    db.refresh(order)
    return order


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_status(order_id: uuid.UUID, payload: OrderStatusUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).with_for_update().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    is_owning_rider = current_user.role == UserRole.rider and order.rider_id == current_user.id
    is_admin = current_user.role == UserRole.admin
    if not (is_owning_rider or is_admin):
        raise HTTPException(status_code=403, detail="Only the assigned rider or an Admin can update this order's status")

    allowed_next = ALLOWED_TRANSITIONS.get(order.status, set())
    if payload.status not in allowed_next and not is_admin:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot move from '{order.status.value}' to '{payload.status.value}'",
        )
    # Admin can override (Section 4.2: Status Override), rider must follow the state machine
    if payload.status == OrderStatus.picked_up and not order.price_confirmed_at:
        raise HTTPException(status_code=400, detail="Rider must verify item size and sender must confirm the final fee before pickup")

    order.status = payload.status
    _log(db, order.id, payload.status, payload.note)

    # PRD 5.6: crediting the rider's wallet when cash actually changes hands
    completion_statuses = {OrderStatus.delivered, OrderStatus.dropped_at_terminal}
    if payload.status in completion_statuses and order.rider_id:
        collected = order.cod_amount
        if order.fee_payer.value == "recipient":
            collected += order.delivery_fee

        if collected > 0:
            rider_profile = db.query(RiderProfile).filter(RiderProfile.user_id == order.rider_id).first()
            already_recorded = db.query(WalletTransaction).filter(
                WalletTransaction.order_id == order.id,
                WalletTransaction.type == TransactionType.collection,
            ).first()
            if rider_profile and not already_recorded:
                rider_profile.wallet_balance = (rider_profile.wallet_balance or 0) + collected
                db.add(WalletTransaction(
                    rider_user_id=order.rider_id,
                    order_id=order.id,
                    type=TransactionType.collection,
                    amount=collected,
                    note=f"Collected on order {order.id} ({payload.status.value})",
                ))

    # COD is a separate liability to the approved partner sender.  The ledger,
    # rather than a mutable balance column, remains the settlement source of truth.
    if payload.status in completion_statuses and order.cod_amount > 0:
        partner = db.query(PartnerProfile).filter(PartnerProfile.user_id == order.sender_id).first()
        existing_credit = db.query(PartnerLedgerEntry).filter(
            PartnerLedgerEntry.order_id == order.id,
            PartnerLedgerEntry.type == PartnerLedgerEntryType.cod_credit,
        ).first()
        if partner and not existing_credit:
            db.add(PartnerLedgerEntry(
                partner_user_id=partner.user_id,
                order_id=order.id,
                type=PartnerLedgerEntryType.cod_credit,
                amount=order.cod_amount,
                status=PartnerLedgerEntryStatus.on_hold,
                available_at=datetime.utcnow() + timedelta(hours=settings.dispute_window_hours),
                note=f"COD held until the dispute window expires ({payload.status.value})",
            ))

    # A recipient-paid fee is cash the rider has collected. Sender-paid fees
    # need their own payment-confirmation flow and are not treated as cash here.
    if payload.status in completion_statuses and order.delivery_fee > 0 and order.fee_payer.value == "recipient":
        existing_fee = db.query(PlatformLedgerEntry).filter(
            PlatformLedgerEntry.order_id == order.id,
            PlatformLedgerEntry.type == PlatformLedgerEntryType.delivery_fee_revenue,
        ).first()
        if not existing_fee:
            db.add(PlatformLedgerEntry(
                order_id=order.id,
                rider_user_id=order.rider_id,
                partner_user_id=order.sender_id if order.cod_amount > 0 else None,
                type=PlatformLedgerEntryType.delivery_fee_revenue,
                amount=order.delivery_fee,
                note=f"Delivery-fee revenue for order {order.id}",
            ))

    if payload.status in completion_statuses and order.rider_id:
        existing_earning = db.query(RiderEarning).filter(RiderEarning.order_id == order.id).first()
        if not existing_earning:
            rate = (
                db.query(RiderCompensationRate)
                .filter(RiderCompensationRate.effective_from <= datetime.utcnow().date())
                .order_by(RiderCompensationRate.effective_from.desc())
                .first()
            )
            if not rate:
                raise HTTPException(
                    status_code=400,
                    detail="No active rider per-way compensation rate has been configured",
                )
            db.add(RiderEarning(
                rider_user_id=order.rider_id,
                order_id=order.id,
                amount=rate.per_completed_way_mmk,
                note=f"Completed order {order.id}; rate effective {rate.effective_from.isoformat()}",
            ))

    db.commit()
    db.refresh(order)
    return order


@router.patch("/{order_id}/cancel", response_model=OrderOut)
def cancel_order(order_id: uuid.UUID, payload: OrderCancelRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).with_for_update().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    is_owner = current_user.role == UserRole.sender and order.sender_id == current_user.id
    is_admin = current_user.role == UserRole.admin
    if not (is_owner or is_admin):
        raise HTTPException(status_code=403, detail="Only the Sender who created this order or an Admin can cancel it")
    if is_admin and not payload.reason:
        raise HTTPException(status_code=400, detail="Admin cancellation requires a recorded reason")

    if order.status == OrderStatus.pending:
        pass  # Sender self-service cancellation, no approval needed (PRD 5.4)
    elif order.status == OrderStatus.assigned:
        if not is_admin:
            raise HTTPException(status_code=400, detail="Cancelling an assigned order requires Admin approval")
    else:
        raise HTTPException(
            status_code=400,
            detail="Order has already been picked up and cannot be self-cancelled; use the Failed Delivery flow instead",
        )

    order.status = OrderStatus.cancelled
    order.cancel_reason = payload.reason
    _log(db, order.id, OrderStatus.cancelled, payload.reason)
    db.commit()
    db.refresh(order)
    return order
