"""
Integration tests for walk-in order flows (staff creating orders for
customers without accounts).

Real route: POST /api/v1/orders/walkin (staff only)
"""
import pytest


def d2d_quote_payload():
    return {
        "delivery_mode": "door_to_door",
        "destination_city": "Yangon",
        "destination_township": "kamayut",
        "dropoff_address": "789 Destination St",
        "dropoff_lat": 16.8500,
        "dropoff_lng": 96.1800,
    }


def create_walkin_order(client, staff_headers, db_session, **overrides):
    """Helper: create zone + quote + walk-in order. Returns response."""
    from tests.conftest import create_delivery_zone

    create_delivery_zone(db_session)
    quote = client.post("/api/v1/quotes", headers=staff_headers, json=d2d_quote_payload()).json()

    payload = {
        "quote_id": quote["id"],
        "walkin_sender_name": "Ma Aye Aye",
        "walkin_sender_phone": "09888888888",
        "recipient_name": "Ko Ko",
        "recipient_phone": "09777777777",
        "pickup_address": "123 Office St",
        "pickup_lat": 16.8409,
        "pickup_lng": 96.1735,
        "item_value": 50000,
        "cod_amount": 0,
        "authorized_max_fee_mmk": float(quote["estimated_fee_mmk"]),
        "terms_accepted": True,
    }
    payload.update(overrides)

    return client.post("/api/v1/orders/walkin", headers=staff_headers, json=payload)


class TestWalkinOrderCreation:
    """Test walk-in order creation by staff."""

    def test_staff_can_create_walkin_order(self, client, staff_headers, db_session):
        response = create_walkin_order(client, staff_headers, db_session)

        assert response.status_code == 201, response.text
        data = response.json()
        assert data["is_walkin"] is True
        assert data["walkin_sender_name"] == "Ma Aye Aye"
        assert data["walkin_sender_phone"] == "09888888888"
        assert data["created_by_staff_id"] is not None
        assert data["status"] == "pending"

    def test_walkin_order_cannot_have_cod(self, client, staff_headers, db_session):
        """Walk-in orders cannot have COD - customer pays at office."""
        response = create_walkin_order(client, staff_headers, db_session, cod_amount=10000)

        assert response.status_code == 400
        assert "cod" in response.json()["detail"].lower()

    def test_sender_cannot_create_walkin_order(self, client, sender_headers, db_session):
        """Regular senders cannot use the walk-in endpoint."""
        response = create_walkin_order(client, sender_headers, db_session)

        assert response.status_code == 403
        assert "staff" in response.json()["detail"].lower()

    def test_rider_cannot_create_walkin_order(self, client, rider_headers, db_session):
        """Riders cannot use the walk-in endpoint."""
        from tests.conftest import create_delivery_zone

        create_delivery_zone(db_session)
        response = client.post(
            "/api/v1/orders/walkin",
            headers=rider_headers,
            json={
                "quote_id": "550e8400-e29b-41d4-a716-446655440000",
                "walkin_sender_name": "Test",
                "walkin_sender_phone": "09888888888",
                "recipient_name": "Test",
                "recipient_phone": "09777777777",
                "pickup_address": "Test",
                "pickup_lat": 16.8409,
                "pickup_lng": 96.1735,
                "item_value": 50000,
                "cod_amount": 0,
                "authorized_max_fee_mmk": 4000,
                "terms_accepted": True,
            },
        )

        assert response.status_code == 403

    def test_admin_cannot_create_walkin_order(self, client, admin_headers, rider_headers, db_session):
        """Admins are not staff; they cannot use the walk-in endpoint either."""
        from tests.conftest import create_delivery_zone

        # Admins also can't request quotes (sender/staff only), so use any quote UUID -
        # the role check fires first.
        create_delivery_zone(db_session)
        response = client.post(
            "/api/v1/orders/walkin",
            headers=admin_headers,
            json={
                "quote_id": "550e8400-e29b-41d4-a716-446655440000",
                "walkin_sender_name": "Test",
                "walkin_sender_phone": "09888888888",
                "recipient_name": "Test",
                "recipient_phone": "09777777777",
                "pickup_address": "Test",
                "pickup_lat": 16.8409,
                "pickup_lng": 96.1735,
                "item_value": 50000,
                "cod_amount": 0,
                "authorized_max_fee_mmk": 4000,
                "terms_accepted": True,
            },
        )

        assert response.status_code == 403

    def test_walkin_order_must_accept_terms(self, client, staff_headers, db_session):
        response = create_walkin_order(client, staff_headers, db_session, terms_accepted=False)

        assert response.status_code == 400
        assert "terms" in response.json()["detail"].lower()

    def test_walkin_requires_customer_name_and_phone(self, client, staff_headers, db_session):
        """Missing walk-in customer details fail validation."""
        from tests.conftest import create_delivery_zone

        create_delivery_zone(db_session)
        quote = client.post("/api/v1/quotes", headers=staff_headers, json=d2d_quote_payload()).json()

        response = client.post(
            "/api/v1/orders/walkin",
            headers=staff_headers,
            json={
                "quote_id": quote["id"],
                # missing walkin_sender_name / walkin_sender_phone
                "recipient_name": "Ko Ko",
                "recipient_phone": "09777777777",
                "pickup_address": "123 Office St",
                "pickup_lat": 16.8409,
                "pickup_lng": 96.1735,
                "item_value": 50000,
                "cod_amount": 0,
                "authorized_max_fee_mmk": float(quote["maximum_fee_mmk"]),
                "terms_accepted": True,
            },
        )

        assert response.status_code == 422


class TestWalkinVsRegularOrders:
    """Verify walk-in feature does not break the regular flow."""

    def test_regular_sender_orders_unaffected(self, client, sender_headers, db_session):
        """Sender order creation works and has no walk-in markers."""
        from tests.conftest import create_delivery_zone

        create_delivery_zone(db_session)
        quote = client.post(
            "/api/v1/quotes",
            headers=sender_headers,
            json=d2d_quote_payload(),
        ).json()

        response = client.post(
            "/api/v1/orders",
            headers=sender_headers,
            json={
                "quote_id": quote["id"],
                "recipient_name": "U Ba",
                "recipient_phone": "09777777771",
                "pickup_address": "123 Pickup St",
                "pickup_lat": 16.8409,
                "pickup_lng": 96.1735,
                "item_value": 30000,
                "cod_amount": 0,
                "authorized_max_fee_mmk": float(quote["maximum_fee_mmk"]),
                "terms_accepted": True,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["is_walkin"] is False
        assert data["walkin_sender_name"] is None
        assert data["created_by_staff_id"] is None


class TestWalkinFullLifecycle:
    """Walk-in orders follow the same delivery lifecycle."""

    def test_walkin_order_full_lifecycle(
        self, client, staff_headers, rider, rider_headers, admin_headers, db_session
    ):
        """Walk-in order: created → assigned → verified → confirmed → picked up → delivered."""
        from app.models.pricing import ItemSizeRate

        client.post(
            "/api/v1/admin/item-size-rates",
            headers=admin_headers,
            json={"name": "medium", "surcharge_mmk": 1000, "active": True},
        )

        response = create_walkin_order(client, staff_headers, db_session)
        assert response.status_code == 201
        order = response.json()
        order_id = order["id"]

        # Admin assigns a rider
        r = client.patch(
            f"/api/v1/orders/{order_id}/assign",
            headers=admin_headers,
            json={"rider_id": str(rider.id)},
        )
        assert r.status_code == 200

        # Rider verifies item size
        r = client.patch(
            f"/api/v1/orders/{order_id}/verify-item-size",
            headers=rider_headers,
            json={"item_size": "medium"},
        )
        assert r.status_code == 200

        # Walk-in orders have no real sender account to confirm;
        # admin approves the final fee instead.
        r = client.patch(
            f"/api/v1/orders/{order_id}/approve-final-fee",
            headers=admin_headers,
            json={"reason": "Walk-in fee approved at office"},
        )
        assert r.status_code == 200

        # Pickup + deliver
        r = client.patch(
            f"/api/v1/orders/{order_id}/status",
            headers=rider_headers,
            json={"status": "picked_up"},
        )
        assert r.status_code == 200

        r = client.patch(
            f"/api/v1/orders/{order_id}/status",
            headers=rider_headers,
            json={"status": "delivered"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "delivered"
