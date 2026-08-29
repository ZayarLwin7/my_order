"""
Seed demo users for local development.

Inserts one user per role with known credentials so the Flutter app's
role-gated screens and the API can be exercised end-to-end:

    Role      Phone           Password           Extra state
    admin     09011111111     Password123456     -
    customer  09022222222     Password123456     (sender)
    rider     09033333333     Password123456     approved + active rider profile
    staff     09044444444     Password123456     -

Idempotent: re-running updates the password but does not duplicate rows.

Usage:
    cd my-order-backend
    source venv/bin/activate
    python scripts/seed_users.py

Requires DATABASE_URL (and the rest of the app settings) from the environment
or .env. With `python-dotenv` installed, .env is loaded automatically.
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone

# Make the app package importable when run as a script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # python-dotenv optional
    pass

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base  # noqa: F401  (ensures models are registered)
from app.config import settings
from app.auth_utils import hash_password
from app.models.user import User, UserRole
from app.models.rider import RiderProfile, ApplicationStatus


# (phone, name, role, password)
SEED_USERS = [
    ("09011111111", "Admin User", UserRole.admin, "Password123456"),
    ("09022222222", "Customer User", UserRole.sender, "Password123456"),
    ("09033333333", "Rider User", UserRole.rider, "Password123456"),
    ("09044444444", "Staff User", UserRole.staff, "Password123456"),
]

RIDER_NRC = "12/ABC(N)123456"
RIDER_VEHICLE_PLATE = "YGN-1234"


def main() -> None:
    database_url = settings.database_url
    if not database_url:
        print("ERROR: DATABASE_URL is not set. Copy .env.example to .env and set it.")
        sys.exit(1)

    engine = create_engine(database_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    session = Session()

    try:
        for phone, name, role, password in SEED_USERS:
            user = session.query(User).filter(User.phone == phone).first()
            if user is None:
                user = User(
                    id=uuid.uuid4(),
                    name=name,
                    phone=phone,
                    password_hash=hash_password(password),
                    role=role,
                    created_at=datetime.now(timezone.utc),
                )
                session.add(user)
                session.flush()
                print(f"Created {role.value:7} {name} ({phone})")
            else:
                # Keep credentials fresh on re-runs; don't change role.
                user.password_hash = hash_password(password)
                print(f"Updated {role.value:7} {name} ({phone})")

            # For riders, ensure an approved + active profile exists so the
            # Flutter rider app shows the dashboard instead of the apply screen.
            if role == UserRole.rider:
                profile = (
                    session.query(RiderProfile)
                    .filter(RiderProfile.user_id == user.id)
                    .first()
                )
                if profile is None:
                    profile = RiderProfile(
                        id=uuid.uuid4(),
                        user_id=user.id,
                        nrc=RIDER_NRC,
                        vehicle_plate=RIDER_VEHICLE_PLATE,
                        application_status=ApplicationStatus.approved,
                        active_status=True,
                        suspended=False,
                    )
                    session.add(profile)
                    print(f"  + rider profile (approved, active) for {phone}")

        session.commit()
        print("\nSeed complete. Log in with any of the accounts above.")
        print("Password for all accounts: Password123456")
    finally:
        session.close()


if __name__ == "__main__":
    main()
