"""
Seed reference data needed for the order lifecycle to work end-to-end.

Inserts (idempotently):
  - one active delivery zone (Yangon / Kamayut)        -> delivery_zones
  - one active item-size rate ("medium")               -> item_size_rates
  - one rider compensation rate (per completed way)    -> rider_compensation_rates

These are required before an order can be quoted, item-size verified, and
reached "delivered" (the backend refuses delivery without a compensation rate,
and item-size verification needs an active item-size rate).

The compensation rate requires a `created_by_user_id`; this script looks up the
admin demo user (09711111111) or falls back to the first admin in the DB.

Idempotent: re-running does not create duplicate rows.

Usage:
    cd my-order-backend
    source venv/bin/activate
    python scripts/seed_reference_data.py

Reads DATABASE_URL (and the rest of app settings) from the environment or .env.
"""
from __future__ import annotations

import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # python-dotenv optional
    pass

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base  # noqa: F401  (registers models)
from app.config import settings
from app.models.pricing import DeliveryZone, ItemSizeRate
from app.models.rider_earnings import RiderCompensationRate
from app.models.user import User, UserRole


# Fixed values so the script is deterministic and idempotent.
ZONE_CITY = "Yangon"
ZONE_TOWNSHIP = "Kamayut"
ZONE_SURCHARGE_MMK = 500

SIZE_RATE_NAME = "medium"
SIZE_RATE_SURCHARGE_MMK = 1000

COMP_RATE_PER_WAY_MMK = 2000
COMP_RATE_EFFECTIVE_FROM = date(2026, 1, 1)  # fixed date => idempotent

ADMIN_DEMO_PHONE = "09711111111"


def _force_public_schema(engine) -> None:
    """Supabase has both public.users and auth.users; force public so we never
    touch Supabase Auth's tables."""
    @event.listens_for(engine, "connect")
    def _set_schema(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        cur.execute("SET search_path TO public")
        cur.close()


def _resolve_admin_id(session) -> str:
    admin = (
        session.query(User)
        .filter(User.phone == ADMIN_DEMO_PHONE)
        .first()
    )
    if admin is None:
        admin = session.query(User).filter(User.role == UserRole.admin).first()
    if admin is None:
        raise RuntimeError("No admin user found. Run scripts/seed_users.py first.")
    return admin.id


def main() -> None:
    database_url = settings.database_url
    if not database_url:
        print("ERROR: DATABASE_URL is not set. Copy .env.example to .env and set it.")
        sys.exit(1)

    engine = create_engine(database_url, pool_pre_ping=True)
    _force_public_schema(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    session = Session()

    try:
        # 1) Delivery zone (unique on city+township)
        zone = (
            session.query(DeliveryZone)
            .filter(DeliveryZone.city == ZONE_CITY, DeliveryZone.township == ZONE_TOWNSHIP)
            .first()
        )
        if zone is None:
            zone = DeliveryZone(
                city=ZONE_CITY,
                township=ZONE_TOWNSHIP,
                surcharge_mmk=ZONE_SURCHARGE_MMK,
                active=True,
            )
            session.add(zone)
            session.flush()
            print(f"Created delivery zone {ZONE_CITY}/{ZONE_TOWNSHIP} (surcharge {ZONE_SURCHARGE_MMK} MMK)")
        else:
            print(f"Delivery zone {ZONE_CITY}/{ZONE_TOWNSHIP} already exists")

        # 2) Item-size rate (unique on name)
        size = (
            session.query(ItemSizeRate)
            .filter(ItemSizeRate.name == SIZE_RATE_NAME)
            .first()
        )
        if size is None:
            size = ItemSizeRate(
                name=SIZE_RATE_NAME,
                surcharge_mmk=SIZE_RATE_SURCHARGE_MMK,
                active=True,
            )
            session.add(size)
            session.flush()
            print(f"Created item-size rate '{SIZE_RATE_NAME}' (surcharge {SIZE_RATE_SURCHARGE_MMK} MMK)")
        else:
            print(f"Item-size rate '{SIZE_RATE_NAME}' already exists")

        # 3) Rider compensation rate (unique on effective_from)
        admin_id = _resolve_admin_id(session)
        comp = (
            session.query(RiderCompensationRate)
            .filter(RiderCompensationRate.effective_from == COMP_RATE_EFFECTIVE_FROM)
            .first()
        )
        if comp is None:
            comp = RiderCompensationRate(
                per_completed_way_mmk=COMP_RATE_PER_WAY_MMK,
                effective_from=COMP_RATE_EFFECTIVE_FROM,
                created_by_user_id=admin_id,
            )
            session.add(comp)
            session.flush()
            print(f"Created compensation rate {COMP_RATE_PER_WAY_MMK} MMK/way effective {COMP_RATE_EFFECTIVE_FROM}")
        else:
            print(f"Compensation rate effective {COMP_RATE_EFFECTIVE_FROM} already exists")

        session.commit()
        print("\nReference data seed complete.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
