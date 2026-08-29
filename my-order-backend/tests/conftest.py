"""
Shared test fixtures and configuration for integration tests.

Provides:
- Test database setup with transaction rollback
- Factory functions for creating test data
- Common fixtures for users, tokens, and API client
"""
import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.database import Base
from app.main import app
from app.dependencies import get_db
from app.models.user import User, UserRole
from app.models.rider import RiderProfile, ApplicationStatus
from app.models.partner import PartnerProfile
from app.models.pricing import DeliveryZone
from app.auth_utils import hash_password, create_access_token


# Test database URL - override with TEST_DATABASE_URL env var
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/my_order_test"
)

test_engine = create_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,   # reconnect on dropped connections (remote DBs)
    pool_recycle=300,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def setup_test_database():
    """Create all tables before integration tests, drop after.

    Only activated when a test requests db_session/client (integration tests);
    plain unit tests never touch the database.
    """
    """Create all tables before tests run, drop after all tests complete.

    Uses use_altered FKeys workaround: orders <-> delivery_quotes reference each
    other, so drop must happen in two passes with FK enforcement disabled.
    """
    Base.metadata.create_all(bind=test_engine)
    yield
    # orders <-> delivery_quotes circular FK prevents plain drop_all;
    # DROP ... CASCADE handles the dependency order for us.
    with test_engine.begin() as conn:
        conn.execute(text(
            "DROP TABLE IF EXISTS " + ", ".join(
                f'"{t.name}"' for t in reversed(Base.metadata.sorted_tables)
            ) + " CASCADE"
        ))


@pytest.fixture(scope="function")
def db_session(setup_test_database):
    """
    Transactional database session per test.
    Everything is rolled back after each test.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Test client with database dependency override."""
    # Reset the in-memory auth rate limiter so tests are isolated from
    # each other (all TestClient requests share the same host key).
    from app.security import auth_limiter
    auth_limiter._requests.clear()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ============================================================================
# Factory Functions
# ============================================================================

def create_user(
    db: Session,
    name: str = "Test User",
    phone: str = "09111111111",
    password: str = "testpassword123",
    role: UserRole = UserRole.sender
) -> User:
    """Create a test user."""
    user = User(
        name=name,
        phone=phone,
        password_hash=hash_password(password),
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_sender(db: Session, phone: str = "09222222222") -> User:
    return create_user(db, name="Test Sender", phone=phone, role=UserRole.sender)


def create_rider(db: Session, phone: str = "09333333333", approved: bool = True) -> User:
    """Create a rider user with an approved profile."""
    user = create_user(db, name="Test Rider", phone=phone, role=UserRole.rider)
    profile = RiderProfile(
        user_id=user.id,
        nrc="12/ABC(N)123456",
        vehicle_plate="YGN-1234",
        application_status=ApplicationStatus.approved if approved else ApplicationStatus.pending_review,
        active_status=approved,
        suspended=False,
        wallet_balance=0,
    )
    db.add(profile)
    db.commit()
    return user


def create_staff(db: Session, phone: str = "09444444444") -> User:
    return create_user(db, name="Test Staff", phone=phone, role=UserRole.staff)


def create_admin(db: Session, phone: str = "09555555555") -> User:
    return create_user(db, name="Test Admin", phone=phone, role=UserRole.admin)


def create_partner(db: Session, phone: str = "09666666666", approved: bool = True) -> User:
    """Create a sender with an active partner profile."""
    user = create_sender(db, phone=phone)
    profile = PartnerProfile(
        user_id=user.id,
        business_name="Test Business",
        business_address="123 Business St",
        contact_phone=phone,
        active_status=approved,
        suspended=False,
        delivery_discount_mmk=0,
    )
    db.add(profile)
    db.commit()
    return user


def create_delivery_zone(db: Session, city: str = "yangon", township: str = "kamayut", surcharge: int = 500) -> DeliveryZone:
    """Create an active delivery zone (required for door-to-door quotes)."""
    zone = DeliveryZone(
        city=city,
        township=township,
        surcharge_mmk=surcharge,
        active=True,
    )
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


def get_auth_token(user: User) -> str:
    return create_access_token({"sub": str(user.id), "role": user.role.value})


def get_auth_headers(user: User) -> dict:
    return {"Authorization": f"Bearer {get_auth_token(user)}"}


# ============================================================================
# Ready-to-use fixtures
# ============================================================================

@pytest.fixture
def sender(db_session):
    return create_sender(db_session)


@pytest.fixture
def sender_token(sender):
    return get_auth_token(sender)


@pytest.fixture
def sender_headers(sender):
    return get_auth_headers(sender)


@pytest.fixture
def rider(db_session):
    return create_rider(db_session)


@pytest.fixture
def rider_token(rider):
    return get_auth_token(rider)


@pytest.fixture
def rider_headers(rider):
    return get_auth_headers(rider)


@pytest.fixture
def staff(db_session):
    return create_staff(db_session)


@pytest.fixture
def staff_token(staff):
    return get_auth_token(staff)


@pytest.fixture
def staff_headers(staff):
    return get_auth_headers(staff)


@pytest.fixture
def admin(db_session):
    return create_admin(db_session)


@pytest.fixture
def admin_token(admin):
    return get_auth_token(admin)


@pytest.fixture
def admin_headers(admin):
    return get_auth_headers(admin)


@pytest.fixture
def partner(db_session):
    return create_partner(db_session)


@pytest.fixture
def partner_token(partner):
    return get_auth_token(partner)


@pytest.fixture
def partner_headers(partner):
    return get_auth_headers(partner)


@pytest.fixture
def delivery_zone(db_session):
    """Active Yangon delivery zone so door-to-door quotes work."""
    return create_delivery_zone(db_session)
