import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies import get_current_user, get_db, require_admin
from app.models.order import DeliveryMode, FeePayer
from app.models.partner import PartnerProfile
from app.models.pricing import DeliveryQuote, DeliveryZone, ItemSizeRate
from app.models.user import User, UserRole
from app.schemas.pricing import (
    DeliveryQuoteCreate,
    DeliveryQuoteOut,
    DeliveryZoneOut,
    DeliveryZoneUpsert,
    ItemSizeRateOut,
    ItemSizeRateUpsert,
    PartnerDiscountRequest,
)

router = APIRouter(tags=["Pricing"])


@router.post("/quotes", response_model=DeliveryQuoteOut, status_code=status.HTTP_201_CREATED)
def create_quote(
    payload: DeliveryQuoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.sender, UserRole.staff):
        raise HTTPException(status_code=403, detail="Only Sender or Staff accounts can request delivery quotes")
    base_fee = Decimal(str(settings.delivery_base_fee_mmk))
    zone_surcharge = Decimal("0")
    if payload.delivery_mode == DeliveryMode.door_to_door:
        if payload.destination_city.strip().lower() not in {"yangon", "mandalay"}:
            raise HTTPException(status_code=400, detail="Door-to-Door delivery is available only in Yangon and Mandalay")
        zone = db.query(DeliveryZone).filter(
            DeliveryZone.city.ilike(payload.destination_city.strip()),
            DeliveryZone.township.ilike(payload.destination_township.strip()),
            DeliveryZone.active.is_(True),
        ).first()
        if not zone:
            raise HTTPException(status_code=400, detail="Destination township is not an active delivery zone")
        zone_surcharge = zone.surcharge_mmk

    partner = db.query(PartnerProfile).filter(PartnerProfile.user_id == current_user.id).first()
    discount = partner.delivery_discount_mmk if partner and partner.active_status and not partner.suspended else Decimal("0")
    estimated_fee = max(Decimal("0"), base_fee + zone_surcharge - discount)
    largest_item_surcharge = Decimal(
        db.query(func.coalesce(func.max(ItemSizeRate.surcharge_mmk), 0))
        .filter(ItemSizeRate.active.is_(True))
        .scalar()
        or 0
    )
    quote = DeliveryQuote(
        sender_id=current_user.id,
        delivery_mode=payload.delivery_mode.value,
        destination_city=payload.destination_city.strip() if payload.destination_city else None,
        destination_township=payload.destination_township.strip() if payload.destination_township else None,
        destination_town=payload.destination_town.strip() if payload.destination_town else None,
        dropoff_address=payload.dropoff_address.strip() if payload.dropoff_address else None,
        dropoff_lat=payload.dropoff_lat,
        dropoff_lng=payload.dropoff_lng,
        terminal_name=payload.terminal_name.strip() if payload.terminal_name else None,
        bus_line=payload.bus_line.strip() if payload.bus_line else None,
        fee_payer=(FeePayer.sender if payload.delivery_mode == DeliveryMode.bus_terminal else payload.fee_payer).value,
        base_fee_mmk=base_fee,
        zone_surcharge_mmk=zone_surcharge,
        partner_discount_mmk=discount,
        estimated_fee_mmk=estimated_fee,
        maximum_fee_mmk=estimated_fee + largest_item_surcharge,
        expires_at=datetime.utcnow() + timedelta(minutes=settings.quote_expire_minutes),
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)
    return quote


@router.get("/quotes/{quote_id}", response_model=DeliveryQuoteOut)
def get_quote(quote_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    quote = db.query(DeliveryQuote).filter(DeliveryQuote.id == quote_id, DeliveryQuote.sender_id == current_user.id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote


@router.get("/admin/delivery-zones", response_model=list[DeliveryZoneOut])
def list_zones(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return db.query(DeliveryZone).order_by(DeliveryZone.city, DeliveryZone.township).all()


@router.put("/admin/delivery-zones/{zone_id}", response_model=DeliveryZoneOut)
def update_zone(zone_id: uuid.UUID, payload: DeliveryZoneUpsert, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    zone = db.query(DeliveryZone).filter(DeliveryZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Delivery zone not found")
    for key, value in payload.model_dump().items():
        setattr(zone, key, value.strip() if isinstance(value, str) else value)
    db.commit()
    db.refresh(zone)
    return zone


@router.post("/admin/delivery-zones", response_model=DeliveryZoneOut, status_code=status.HTTP_201_CREATED)
def create_zone(payload: DeliveryZoneUpsert, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if payload.city.strip().lower() not in {"yangon", "mandalay"}:
        raise HTTPException(status_code=400, detail="Delivery zones can only be created for Yangon or Mandalay")
    if db.query(DeliveryZone).filter(DeliveryZone.city.ilike(payload.city.strip()), DeliveryZone.township.ilike(payload.township.strip())).first():
        raise HTTPException(status_code=400, detail="This city and township zone already exists")
    zone = DeliveryZone(**{key: value.strip() if isinstance(value, str) else value for key, value in payload.model_dump().items()})
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


@router.get("/admin/item-size-rates", response_model=list[ItemSizeRateOut])
def list_item_size_rates(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return db.query(ItemSizeRate).order_by(ItemSizeRate.name).all()


@router.post("/admin/item-size-rates", response_model=ItemSizeRateOut, status_code=status.HTTP_201_CREATED)
def create_item_size_rate(payload: ItemSizeRateUpsert, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if db.query(ItemSizeRate).filter(ItemSizeRate.name.ilike(payload.name.strip())).first():
        raise HTTPException(status_code=400, detail="Item-size rate already exists")
    rate = ItemSizeRate(**{key: value.strip() if isinstance(value, str) else value for key, value in payload.model_dump().items()})
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate


@router.put("/admin/item-size-rates/{rate_id}", response_model=ItemSizeRateOut)
def update_item_size_rate(rate_id: uuid.UUID, payload: ItemSizeRateUpsert, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    rate = db.query(ItemSizeRate).filter(ItemSizeRate.id == rate_id).first()
    if not rate:
        raise HTTPException(status_code=404, detail="Item-size rate not found")
    for key, value in payload.model_dump().items():
        setattr(rate, key, value.strip() if isinstance(value, str) else value)
    db.commit()
    db.refresh(rate)
    return rate


@router.patch("/admin/partners/{partner_user_id}/delivery-discount", status_code=status.HTTP_204_NO_CONTENT)
def set_partner_discount(partner_user_id: uuid.UUID, payload: PartnerDiscountRequest, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    partner = db.query(PartnerProfile).filter(PartnerProfile.user_id == partner_user_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner profile not found")
    partner.delivery_discount_mmk = payload.delivery_discount_mmk
    db.commit()
