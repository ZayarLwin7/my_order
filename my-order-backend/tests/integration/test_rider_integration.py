"""
Integration tests for rider flows.

Tests:
- Rider application
- Rider approval/rejection
- Item size verification
- Status updates
- Rider permissions
"""
import pytest


class TestRiderApplication:
    """Test rider application process."""

    def test_rider_can_apply(self, client, db_session):
        """Rider can submit application."""
        from tests.conftest import create_user
        from app.models.user import UserRole

        # Create rider account without profile
        rider = create_user(db_session, phone="09555555550", role=UserRole.rider)
        from tests.conftest import get_auth_headers
        headers = get_auth_headers(rider)

        response = client.post(
            "/api/v1/riders/apply",
            headers=headers,
            json={
                "nrc": "12/ABC(N)123456",
                "license_number": "LIC-12345",
                "vehicle_plate": "YGN-5678"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending_review"
        assert data["nrc"] == "12/ABC(N)123456"

    def test_sender_cannot_apply_as_rider(self, client, sender_headers):
        """Senders cannot submit rider applications."""
        response = client.post(
            "/api/v1/riders/apply",
            headers=sender_headers,
            json={
                "nrc": "12/ABC(N)123456",
                "license_number": "LIC-12345",
                "vehicle_plate": "YGN-5678"
            }
        )

        assert response.status_code == 403

    def test_cannot_apply_twice(self, client, db_session):
        """Cannot submit multiple applications."""
        from tests.conftest import create_user
        from app.models.user import UserRole

        rider = create_user(db_session, phone="09555555551", role=UserRole.rider)
        from tests.conftest import get_auth_headers
        headers = get_auth_headers(rider)

        payload = {
            "nrc": "12/ABC(N)123456",
            "license_number": "LIC-12345",
            "vehicle_plate": "YGN-5678"
        }

        # First application
        response1 = client.post("/api/v1/riders/apply", headers=headers, json=payload)
        assert response1.status_code == 201

        # Second application should fail
        response2 = client.post("/api/v1/riders/apply", headers=headers, json=payload)
        assert response2.status_code == 400


class TestRiderApproval:
    """Test rider approval process."""

    def test_admin_can_approve_rider(self, client, admin_headers, db_session):
        """Admin can approve pending rider applications."""
        from tests.conftest import create_user, get_auth_headers
        from app.models.user import UserRole

        # Create a rider and submit an application (so an application row exists).
        rider = create_user(db_session, phone="09555555552", role=UserRole.rider)
        apply_resp = client.post(
            "/api/v1/riders/apply",
            headers=get_auth_headers(rider),
            json={"nrc": "12/ABC(N)123456", "license_number": "LIC-123", "vehicle_plate": "YGN-1234"},
        )
        assert apply_resp.status_code == 201
        application_id = apply_resp.json()["id"]

        # Approve via admin endpoint (keyed on the application id)
        response = client.patch(
            f"/api/v1/riders/{application_id}/approve",
            headers=admin_headers,
            json={},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"

    def test_admin_can_reject_rider(self, client, admin_headers, db_session):
        """Admin can reject rider applications."""
        from tests.conftest import create_user, get_auth_headers
        from app.models.user import UserRole

        rider = create_user(db_session, phone="09555555553", role=UserRole.rider)
        apply_resp = client.post(
            "/api/v1/riders/apply",
            headers=get_auth_headers(rider),
            json={"nrc": "12/ABC(N)123456", "license_number": "LIC-123", "vehicle_plate": "YGN-1234"},
        )
        assert apply_resp.status_code == 201
        application_id = apply_resp.json()["id"]

        response = client.patch(
            f"/api/v1/riders/{application_id}/reject",
            headers=admin_headers,
            json={},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"

    def test_sender_cannot_approve_rider(self, client, sender_headers, db_session):
        """Senders cannot approve riders."""
        from tests.conftest import create_user
        from app.models.user import UserRole

        rider = create_user(db_session, phone="09555555554", role=UserRole.rider)

        response = client.patch(
            f"/api/v1/riders/{rider.id}/approve",
            headers=sender_headers,
            json={"approved": True}
        )

        assert response.status_code == 403

    def test_admin_can_list_all_riders(self, client, admin_headers, rider):
        """Admin can list all riders."""
        response = client.get(
            "/api/v1/riders",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(d["user_id"] == str(rider.id) for d in data)


class TestRiderSuspension:
    """Test rider suspension."""

    def test_admin_can_suspend_rider(self, client, admin_headers, rider):
        """Admin can suspend riders."""
        response = client.patch(
            f"/api/v1/riders/{rider.id}/suspend",
            headers=admin_headers,
            json={
                "suspended": True,
                "reason": "Wallet not reconciled"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["suspended"] is True

    def test_admin_can_unsuspend_rider(self, client, admin_headers, rider):
        """Admin can unsuspend riders."""
        # Suspend first
        client.patch(
            f"/api/v1/riders/{rider.id}/suspend",
            headers=admin_headers,
            json={"suspended": True, "reason": "Test"}
        )

        # Unsuspend
        response = client.patch(
            f"/api/v1/riders/{rider.id}/suspend",
            headers=admin_headers,
            json={"suspended": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["suspended"] is False


class TestItemSizeVerification:
    """Test rider item size verification."""

    def test_rider_can_verify_item_size(self, client, sender_headers, rider, rider_headers, admin_headers, db_session):
        """Rider can verify item size on assigned order."""
        from tests.conftest import create_delivery_zone
        create_delivery_zone(db_session)

        # Create item size rate (correct admin endpoint)
        client.post(
            "/api/v1/admin/item-size-rates",
            headers=admin_headers,
            json={"name": "Medium", "surcharge_mmk": 1000, "active": True},
        )

        # Create and assign order
        quote_response = client.post(
            "/api/v1/quotes",
            headers=sender_headers,
            json={
                "delivery_mode": "door_to_door",
                "destination_city": "Yangon",
                "destination_township": "kamayut",
                "dropoff_address": "Test",
                "dropoff_lat": 16.8500,
                "dropoff_lng": 96.1800,
                "fee_payer": "sender",
            },
        )
        quote = quote_response.json()

        order_response = client.post(
            "/api/v1/orders",
            headers=sender_headers,
            json={
                "quote_id": quote["id"],
                "recipient_name": "Test",
                "recipient_phone": "09777777777",
                "pickup_address": "Test",
                "pickup_lat": 16.8409,
                "pickup_lng": 96.1735,
                "item_value": 50000,
                "cod_amount": 0,
                "authorized_max_fee_mmk": quote["maximum_fee_mmk"],
                "terms_accepted": True,
            },
        )
        order = order_response.json()

        # Assign to rider
        client.patch(
            f"/api/v1/orders/{order['id']}/assign",
            headers=admin_headers,
            json={"rider_id": str(rider.id)},
        )

        # Rider verifies item size (case-insensitive match in backend)
        response = client.patch(
            f"/api/v1/orders/{order['id']}/verify-item-size",
            headers=rider_headers,
            json={"item_size": "Medium"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["item_size"] == "Medium"
        assert float(data["delivery_fee"]) > float(quote["estimated_fee_mmk"])  # Has surcharge

    def test_sender_cannot_verify_item_size(self, client, sender_headers, rider, admin_headers, db_session):
        """Senders cannot verify item size."""
        # Create order and assign
        from tests.conftest import create_delivery_zone
        create_delivery_zone(db_session)
        quote_response = client.post(
            "/api/v1/quotes",
            headers=sender_headers,
            json={
                "delivery_mode": "door_to_door",
                "destination_city": "Yangon",
                "destination_township": "kamayut",
                "dropoff_address": "Test",
                "pickup_lat": 16.8409,
                "pickup_lng": 96.1735,
                "dropoff_lat": 16.8500,
                "dropoff_lng": 96.1800,
                "fee_payer": "sender",
            },
        )
        quote = quote_response.json()

        order_response = client.post(
            "/api/v1/orders",
            headers=sender_headers,
            json={
                "quote_id": quote["id"],
                "recipient_name": "Test",
                "recipient_phone": "09777777777",
                "pickup_address": "Test",
                "pickup_lat": 16.8409,
                "pickup_lng": 96.1735,
                "item_value": 50000,
                "cod_amount": 0,
                "authorized_max_fee_mmk": quote["maximum_fee_mmk"],
                "terms_accepted": True
            }
        )
        order = order_response.json()

        client.patch(
            f"/api/v1/orders/{order['id']}/assign",
            headers=admin_headers,
            json={"rider_id": str(rider.id)}
        )

        # Sender tries to verify (should fail)
        response = client.patch(
            f"/api/v1/orders/{order['id']}/verify-item-size",
            headers=sender_headers,
            json={"item_size": "Medium"}
        )

        assert response.status_code == 403
