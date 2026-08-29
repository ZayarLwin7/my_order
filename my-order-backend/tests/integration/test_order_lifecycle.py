"""
Integration tests for complete order lifecycle (real API shape).

Covers:
- Order creation from quote
- Admin assignment
- Item-size verification and fee confirmation
- Status transitions
- Cancellation
"""
import pytest
from decimal import Decimal


# Payload helpers matching real schemas

def d2d_quote_payload():
    return {
        "delivery_mode": "door_to_door",
        "destination_city": "Yangon",
        "destination_township": "kamayut",
        "dropoff_address": "789 Destination St",
        "dropoff_lat": 16.8500,
        "dropoff_lng": 96.1800,
    }


def order_payload(quote: dict):
    return {
        "quote_id": quote["id"],
        "recipient_name": "Daw Mya",
        "recipient_phone": "09777777777",
        "pickup_address": "123 Pickup St",
        "pickup_lat": 16.8409,
        "pickup_lng": 96.1735,
        "item_value": 50000,
        "cod_amount": 0,
        "authorized_max_fee_mmk": float(quote["maximum_fee_mmk"]),
        "terms_accepted": True,
    }


def create_order_via_api(client, headers, db_session) -> dict:
    """Helper: create delivery zone, get quote, create order. Returns order dict."""
    from tests.conftest import create_delivery_zone

    create_delivery_zone(db_session)
    quote = client.post("/api/v1/quotes", headers=headers, json=d2d_quote_payload()).json()
    response = client.post("/api/v1/orders", headers=headers, json=order_payload(quote))
    assert response.status_code == 201, response.text
    return response.json()


def assign_order(client, admin_headers, order_id, rider_id):
    return client.patch(
        f"/api/v1/orders/{order_id}/assign",
        headers=admin_headers,
        json={"rider_id": str(rider_id)},
    )


class TestOrderCreation:
    """Test order creation flows."""

    def test_sender_can_create_order_with_valid_quote(
        self, client, sender, sender_headers, db_session
    ):
        order = create_order_via_api(client, sender_headers, db_session)

        assert order["status"] == "pending"
        assert order["sender_id"] == str(sender.id)
        assert order["recipient_name"] == "Daw Mya"
        assert order["is_walkin"] is False
        assert order["walkin_sender_name"] is None
        assert order["created_by_staff_id"] is None

    def test_cannot_create_order_with_expired_quote(self, client, sender, sender_headers, db_session):
        """Expired quotes are rejected."""
        from datetime import datetime, timedelta
        from tests.conftest import create_delivery_zone
        from app.models.pricing import DeliveryQuote

        create_delivery_zone(db_session)
        expired = DeliveryQuote(
            sender_id=sender.id,
            delivery_mode="door_to_door",
            destination_city="Yangon",
            destination_township="kamayut",
            dropoff_address="Test",
            dropoff_lat=Decimal("16.8500000"),
            dropoff_lng=Decimal("96.1800000"),
            fee_payer="sender",
            base_fee_mmk=Decimal("3500"),
            zone_surcharge_mmk=Decimal("500"),
            partner_discount_mmk=Decimal("0"),
            estimated_fee_mmk=Decimal("4000"),
            maximum_fee_mmk=Decimal("4000"),
            expires_at=datetime.utcnow() - timedelta(minutes=1),
        )
        db_session.add(expired)
        db_session.commit()

        payload = order_payload({"id": str(expired.id), "maximum_fee_mmk": 4000})
        response = client.post("/api/v1/orders", headers=sender_headers, json=payload)

        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()

    def test_cannot_use_quote_twice(self, client, sender_headers, db_session):
        """Same quote cannot produce two orders."""
        from tests.conftest import create_delivery_zone

        create_delivery_zone(db_session)
        quote = client.post("/api/v1/quotes", headers=sender_headers, json=d2d_quote_payload()).json()
        payload = order_payload(quote)

        r1 = client.post("/api/v1/orders", headers=sender_headers, json=payload)
        assert r1.status_code == 201

        r2 = client.post("/api/v1/orders", headers=sender_headers, json=payload)
        assert r2.status_code == 400
        assert "already been used" in r2.json()["detail"].lower()

    def test_rider_cannot_create_order(self, client, rider_headers):
        response = client.post(
            "/api/v1/orders",
            headers=rider_headers,
            json={**order_payload({"id": "550e8400-e29b-41d4-a716-446655440000", "maximum_fee_mmk": 4000}),
                  "quote_id": "550e8400-e29b-41d4-a716-446655440000"},
        )

        assert response.status_code == 403

    def test_must_accept_terms(self, client, sender_headers, db_session):
        """Orders require terms_accepted=true."""
        from tests.conftest import create_delivery_zone

        create_delivery_zone(db_session)
        quote = client.post("/api/v1/quotes", headers=sender_headers, json=d2d_quote_payload()).json()

        response = client.post(
            "/api/v1/orders",
            headers=sender_headers,
            json={**order_payload(quote), "terms_accepted": False},
        )

        assert response.status_code == 400
        assert "terms" in response.json()["detail"].lower()

    def test_authorized_fee_below_estimate_rejected(self, client, sender_headers, db_session):
        """authorized_max_fee below estimated fee is rejected."""
        from tests.conftest import create_delivery_zone

        create_delivery_zone(db_session)
        quote = client.post("/api/v1/quotes", headers=sender_headers, json=d2d_quote_payload()).json()

        response = client.post(
            "/api/v1/orders",
            headers=sender_headers,
            json={**order_payload(quote), "authorized_max_fee_mmk": 100},
        )

        assert response.status_code == 400
        assert "between" in response.json()["detail"].lower()


class TestOrderAssignment:
    """Test admin assignment to riders."""

    def test_admin_can_assign_order_to_rider(self, client, sender_headers, rider, admin_headers, db_session):
        order = create_order_via_api(client, sender_headers, db_session)

        response = assign_order(client, admin_headers, order["id"], rider.id)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "assigned"
        assert data["rider_id"] == str(rider.id)

    def test_sender_cannot_assign_order(self, client, sender_headers, rider, db_session):
        order = create_order_via_api(client, sender_headers, db_session)

        response = client.patch(
            f"/api/v1/orders/{order['id']}/assign",
            headers=sender_headers,
            json={"rider_id": str(rider.id)},
        )

        assert response.status_code == 403

    def test_suspended_rider_rejected(self, client, sender_headers, rider, admin_headers, db_session):
        """Suspended riders cannot be assigned orders."""
        from app.models.rider import RiderProfile

        profile = db_session.query(RiderProfile).filter(RiderProfile.user_id == rider.id).first()
        profile.suspended = True
        db_session.commit()

        order = create_order_via_api(client, sender_headers, db_session)

        response = assign_order(client, admin_headers, order["id"], rider.id)

        assert response.status_code == 400
        assert "suspended" in response.json()["detail"].lower()


class TestItemSizeVerification:
    """Test item-size verification and final fee flow."""

    def _setup_assigned_order_with_rate(self, client, sender_headers, rider, admin_headers, db_session):
        """Create assigned order + 'medium' rate. Returns order dict.

        Authorizes only the ESTIMATED fee so the item-size surcharge exceeds
        the authorization - forcing the manual confirm/approve step instead of
        the automatic confirmation path.
        """
        client.post(
            "/api/v1/admin/item-size-rates",
            headers=admin_headers,
            json={"name": "medium", "surcharge_mmk": 1000, "active": True},
        )

        from tests.conftest import create_delivery_zone
        create_delivery_zone(db_session)
        quote = client.post("/api/v1/quotes", headers=sender_headers, json=d2d_quote_payload()).json()

        # Authorize only the estimated fee (minimum allowed); any surcharge
        # will exceed this and require explicit confirmation.
        payload = order_payload(quote)
        payload["authorized_max_fee_mmk"] = float(quote["estimated_fee_mmk"])

        response = client.post("/api/v1/orders", headers=sender_headers, json=payload)
        assert response.status_code == 201, response.text
        order = response.json()
        assign_order(client, admin_headers, order["id"], rider.id)
        return order

    def test_rider_can_verify_item_size(self, client, sender_headers, rider, rider_headers, admin_headers, db_session):
        order = self._setup_assigned_order_with_rate(client, sender_headers, rider, admin_headers, db_session)
        original_fee = float(order["delivery_fee"])

        response = client.patch(
            f"/api/v1/orders/{order['id']}/verify-item-size",
            headers=rider_headers,
            json={"item_size": "medium"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["item_size"] == "medium"
        assert float(data["delivery_fee"]) == original_fee + 1000

    def test_sender_confirms_final_fee(self, client, sender_headers, rider, rider_headers, admin_headers, db_session):
        """After size verification, sender confirms the final fee."""
        order = self._setup_assigned_order_with_rate(client, sender_headers, rider, admin_headers, db_session)

        client.patch(
            f"/api/v1/orders/{order['id']}/verify-item-size",
            headers=rider_headers,
            json={"item_size": "medium"},
        )

        response = client.patch(
            f"/api/v1/orders/{order['id']}/confirm-final-fee",
            headers=sender_headers,
        )

        assert response.status_code == 200
        assert response.json()["price_confirmed_at"] is not None

    def test_sender_cannot_verify_item_size(self, client, sender_headers, rider, admin_headers, db_session):
        order = self._setup_assigned_order_with_rate(client, sender_headers, rider, admin_headers, db_session)

        response = client.patch(
            f"/api/v1/orders/{order['id']}/verify-item-size",
            headers=sender_headers,
            json={"item_size": "medium"},
        )

        assert response.status_code == 403

    def test_pickup_blocked_without_fee_confirmation(self, client, sender_headers, rider, rider_headers, admin_headers, db_session):
        """Riders cannot mark picked_up before fee confirmation."""
        order = self._setup_assigned_order_with_rate(client, sender_headers, rider, admin_headers, db_session)

        # Verify size but do NOT confirm fee
        client.patch(
            f"/api/v1/orders/{order['id']}/verify-item-size",
            headers=rider_headers,
            json={"item_size": "medium"},
        )

        response = client.patch(
            f"/api/v1/orders/{order['id']}/status",
            headers=rider_headers,
            json={"status": "picked_up"},
        )

        assert response.status_code == 400
        assert "confirm" in response.json()["detail"].lower()

    def test_full_lifecycle_pending_to_delivered(self, client, sender, sender_headers, rider, rider_headers, admin_headers, db_session):
        """Complete happy path: pending → assigned → picked_up → delivered."""
        order = self._setup_assigned_order_with_rate(client, sender_headers, rider, admin_headers, db_session)

        # Verify + confirm fee
        client.patch(f"/api/v1/orders/{order['id']}/verify-item-size", headers=rider_headers, json={"item_size": "medium"})
        client.patch(f"/api/v1/orders/{order['id']}/confirm-final-fee", headers=sender_headers)

        # Pick up
        r = client.patch(
            f"/api/v1/orders/{order['id']}/status",
            headers=rider_headers,
            json={"status": "picked_up"},
        )
        assert r.status_code == 200

        # Deliver
        r = client.patch(
            f"/api/v1/orders/{order['id']}/status",
            headers=rider_headers,
            json={"status": "delivered"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "delivered"


class TestOrderCancellation:
    """Test order cancellation."""

    def test_sender_can_cancel_pending_order(self, client, sender_headers, db_session):
        order = create_order_via_api(client, sender_headers, db_session)

        response = client.patch(
            f"/api/v1/orders/{order['id']}/cancel",
            headers=sender_headers,
            json={"reason": "Changed my mind"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"

    def test_sender_cannot_cancel_assigned_order(self, client, sender_headers, rider, admin_headers, db_session):
        """Assigned orders need admin approval to cancel."""
        order = create_order_via_api(client, sender_headers, db_session)
        assign_order(client, admin_headers, order["id"], rider.id)

        response = client.patch(
            f"/api/v1/orders/{order['id']}/cancel",
            headers=sender_headers,
            json={"reason": "Too late"},
        )

        assert response.status_code == 400
        assert "admin" in response.json()["detail"].lower()

    def test_other_sender_cannot_cancel(self, client, sender_headers, db_session):
        """A different sender cannot cancel someone else's order."""
        from tests.conftest import create_sender

        order = create_order_via_api(client, sender_headers, db_session)

        other = create_sender(db_session, phone="09999999991")
        other_headers = {"Authorization": f"Bearer other-token"}

        # Use properly signed token for the other user
        from tests.conftest import get_auth_headers
        response = client.patch(
            f"/api/v1/orders/{order['id']}/cancel",
            headers=get_auth_headers(other),
            json={"reason": "Not mine"},
        )

        assert response.status_code == 403


class TestInvalidTransitions:
    """Test state machine enforcement."""

    def test_invalid_transition_rejected(self, client, sender_headers, rider, rider_headers, admin_headers, db_session):
        """pending → delivered directly is not allowed for riders."""
        order = create_order_via_api(client, sender_headers, db_session)
        assign_order(client, admin_headers, order["id"], rider.id)

        response = client.patch(
            f"/api/v1/orders/{order['id']}/status",
            headers=rider_headers,
            json={"status": "delivered"},
        )

        assert response.status_code == 400
