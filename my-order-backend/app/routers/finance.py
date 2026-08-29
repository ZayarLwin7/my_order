from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_admin
from app.models.partner import PartnerLedgerEntry, PartnerLedgerEntryStatus, PlatformLedgerEntry
from app.models.rider import RiderProfile
from app.models.user import User
from app.schemas.finance import PlatformLedgerEntryOut

router = APIRouter(prefix="/finance", tags=["Finance"])


@router.get("/platform-ledger", response_model=list[PlatformLedgerEntryOut])
def list_platform_ledger(
    from_at: datetime | None = None,
    to_at: datetime | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    query = db.query(PlatformLedgerEntry)
    if from_at:
        query = query.filter(PlatformLedgerEntry.created_at >= from_at)
    if to_at:
        query = query.filter(PlatformLedgerEntry.created_at <= to_at)
    return query.order_by(PlatformLedgerEntry.created_at.desc()).all()


@router.get("/reconciliation")
def reconciliation_summary(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    def sum_decimal(query) -> Decimal:
        return Decimal(query.scalar() or 0)

    return {
        "rider_cash_due": sum_decimal(db.query(func.coalesce(func.sum(RiderProfile.wallet_balance), 0))),
        "partner_cod_available": sum_decimal(db.query(func.coalesce(func.sum(PartnerLedgerEntry.amount), 0)).filter(
            PartnerLedgerEntry.status == PartnerLedgerEntryStatus.available,
        )),
        "partner_cod_on_hold": sum_decimal(db.query(func.coalesce(func.sum(PartnerLedgerEntry.amount), 0)).filter(
            PartnerLedgerEntry.status == PartnerLedgerEntryStatus.on_hold,
        )),
        "partner_cod_processing": sum_decimal(db.query(func.coalesce(func.sum(PartnerLedgerEntry.amount), 0)).filter(
            PartnerLedgerEntry.status == PartnerLedgerEntryStatus.processing,
        )),
        "platform_ledger_net": sum_decimal(db.query(func.coalesce(func.sum(PlatformLedgerEntry.amount), 0))),
    }
