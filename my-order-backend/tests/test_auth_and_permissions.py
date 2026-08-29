import uuid

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.dependencies import get_current_user, get_db, require_admin
from app.main import app
from app.models.user import User, UserRole


class FakeQuery:
    def __init__(self, database, model):
        self.database = database
        self.model = model

    def filter(self, *args):
        return self

    def first(self):
        records = self.database.records.get(self.model, [])
        return records[0] if records else None


class FakeDb:
    def __init__(self):
        self.records = {User: []}

    def query(self, model):
        return FakeQuery(self, model)

    def add(self, record):
        if getattr(record, "id", None) is None:
            record.id = uuid.uuid4()
        self.records.setdefault(type(record), []).append(record)

    def commit(self):
        pass

    def refresh(self, record):
        pass


def make_user(role: UserRole) -> User:
    return User(
        id=uuid.uuid4(),
        name="Test User",
        phone="09123456789",
        password_hash="not-used-in-permission-tests",
        role=role,
    )


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def test_public_registration_rejects_admin_role():
    database = FakeDb()
    app.dependency_overrides[get_db] = lambda: database

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "Attacker",
                "phone": "09123456789",
                "password": "a-secure-test-password",
                "role": "admin",
            },
        )

    assert response.status_code == 422


def test_public_registration_allows_sender_only():
    database = FakeDb()
    app.dependency_overrides[get_db] = lambda: database

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "Sender",
                "phone": "09123456789",
                "password": "a-secure-test-password",
                "role": "sender",
            },
        )

    assert response.status_code == 201
    assert response.json()["role"] == "sender"


def test_require_admin_denies_sender_and_allows_admin():
    with pytest.raises(HTTPException) as error:
        require_admin(make_user(UserRole.sender))

    assert error.value.status_code == 403
    assert require_admin(make_user(UserRole.admin)).role == UserRole.admin


def test_rider_cannot_request_sender_quote():
    app.dependency_overrides[get_db] = lambda: FakeDb()
    app.dependency_overrides[get_current_user] = lambda: make_user(UserRole.rider)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/quotes",
            json={
                "delivery_mode": "bus_terminal",
                "destination_town": "Taunggyi",
                "terminal_name": "Aung Mingalar",
                "bus_line": "Yangon-Taunggyi",
            },
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Only Sender or Staff accounts can request delivery quotes"


def test_sender_cannot_access_admin_partner_application_list():
    app.dependency_overrides[get_db] = lambda: FakeDb()
    app.dependency_overrides[get_current_user] = lambda: make_user(UserRole.sender)

    with TestClient(app) as client:
        response = client.get("/api/v1/partners/applications")

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_sender_cannot_submit_rider_application():
    app.dependency_overrides[get_db] = lambda: FakeDb()
    app.dependency_overrides[get_current_user] = lambda: make_user(UserRole.sender)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/riders/apply",
            json={
                "nrc": "12/ABC(N)123456",
                "license_number": "LIC-123",
                "vehicle_plate": "YGN-1234",
            },
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Only rider accounts can submit a rider application"


def test_sender_cannot_manage_delivery_zones():
    app.dependency_overrides[get_db] = lambda: FakeDb()
    app.dependency_overrides[get_current_user] = lambda: make_user(UserRole.sender)

    with TestClient(app) as client:
        response = client.get("/api/v1/admin/delivery-zones")

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_rider_cannot_manage_item_size_rates():
    app.dependency_overrides[get_db] = lambda: FakeDb()
    app.dependency_overrides[get_current_user] = lambda: make_user(UserRole.rider)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/admin/item-size-rates",
            json={"name": "large", "surcharge_mmk": 1500},
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_sender_cannot_access_admin_finance_reconciliation():
    app.dependency_overrides[get_db] = lambda: FakeDb()
    app.dependency_overrides[get_current_user] = lambda: make_user(UserRole.sender)

    with TestClient(app) as client:
        response = client.get("/api/v1/finance/reconciliation")

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_rider_cannot_access_admin_rider_wallet():
    app.dependency_overrides[get_db] = lambda: FakeDb()
    app.dependency_overrides[get_current_user] = lambda: make_user(UserRole.rider)

    with TestClient(app) as client:
        response = client.get(f"/api/v1/riders/{uuid.uuid4()}/wallet")

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_sender_cannot_access_rider_self_earnings():
    app.dependency_overrides[get_db] = lambda: FakeDb()
    app.dependency_overrides[get_current_user] = lambda: make_user(UserRole.sender)

    with TestClient(app) as client:
        response = client.get("/api/v1/riders/me/earnings/summary")

    assert response.status_code == 403
    assert response.json()["detail"] == "Only rider accounts can view rider earnings"


def test_partner_settlement_summary_cannot_be_read_by_unrelated_sender():
    # Partner settlement summaries use the admin-only route for another user;
    # a sender can only use the dedicated /settlements/me route for themselves.
    app.dependency_overrides[get_db] = lambda: FakeDb()
    app.dependency_overrides[get_current_user] = lambda: make_user(UserRole.sender)

    with TestClient(app) as client:
        response = client.get(f"/api/v1/partners/{uuid.uuid4()}/settlement-summary")

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_sender_cannot_create_rider_payout():
    app.dependency_overrides[get_db] = lambda: FakeDb()
    app.dependency_overrides[get_current_user] = lambda: make_user(UserRole.sender)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/riders/payouts",
            json={
                "rider_user_id": str(uuid.uuid4()),
                "period_start": "2026-08-01",
                "period_end": "2026-08-31",
                "salary_amount": 100000,
            },
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"
