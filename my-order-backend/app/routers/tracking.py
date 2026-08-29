import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.order import Order, OrderTrackingLog
from app.models.user import User, UserRole
from app.schemas.tracking import TrackingOut

router = APIRouter(prefix="/tracking", tags=["Tracking"])


@router.get("/{order_id}", response_model=TrackingOut)
def get_tracking(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    is_sender = current_user.role == UserRole.sender and order.sender_id == current_user.id
    is_rider = current_user.role == UserRole.rider and order.rider_id == current_user.id
    if not (is_sender or is_rider or current_user.role == UserRole.admin):
        raise HTTPException(status_code=403, detail="Not authorized to view this order's tracking")

    logs = (
        db.query(OrderTrackingLog)
        .filter(OrderTrackingLog.order_id == order_id)
        .order_by(OrderTrackingLog.created_at)
        .all()
    )

    return TrackingOut(
        order_id=order.id,
        delivery_mode=order.delivery_mode,
        recipient_name=order.recipient_name,
        current_status=order.status,
        terminal_name=order.terminal_name,
        bus_line=order.bus_line,
        milestones=logs,
    )
