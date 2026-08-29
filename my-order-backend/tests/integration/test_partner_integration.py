"""
Integration tests for partner flows.

Tests:
- Partner application
- Partner approval
- COD order restrictions
- Partner permissions
"""
import pytest


class TestPartnerApplication:
    """Test partner application process."""

    def test_sender_can_apply_as_partner(self, client, sender_headers):
        """Sender can apply for partner status."""
        response = client.post(
            "/api/v1/partners/apply",
            headers=sender_headers,
            json={
                "business_name": "My Business",
                "business_address": "123 Business St",
                "contact_phone": "09123456789",
            },
        )

        assert response.status_code == 201
        data = response.json()
        # New applications are pending review and not yet approved.
        assert data["status"] == "pending_review"

    def test_cannot_apply_twice(self, client, sender_headers):
        """Cannot submit multiple partner applications."""
        payload = {
            "business_name": "My Business",
            "business_address": "123 Business St",
            "contact_phone": "09123456789",
        }

        response1 = client.post("/api/v1/partners/apply", headers=sender_headers, json=payload)
        assert response1.status_code == 201

        response2 = client.post("/api/v1/partners/apply", headers=sender_headers, json=payload)
        assert response2.status_code == 400

    def test_admin_can_list_applications(self, client, admin_headers, sender):
        """Admin can list pending partner applications."""
        from tests.conftest import get_auth_headers
        headers = get_auth_headers(sender)

        client.post(
            "/api/v1/partners/apply",
            headers=headers,
            json={
                "business_name": "Test Biz",
                "business_address": "Test Address",
                "contact_phone": "09123456780",
            },
        )

        response = client.get(
            "/api/v1/partners/applications",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_sender_cannot_list_applications(self, client, sender_headers):
        """Senders cannot list partner applications."""
        response = client.get(
            "/api/v1/partners/applications",
            headers=sender_headers,
        )

        assert response.status_code == 403


class TestCODRestrictions:
    """Test COD order restrictions for partners."""

    def test_non_partner_cannot_create_cod_order(self, client, sender_headers, db_session):
        """Regular senders cannot create COD orders."""
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
                "dropoff_lat": 16.8500,
                "dropoff_lng": 96.1800,
                "fee_payer": "sender",
            },
        )
        quote = quote_response.json()

        response = client.post(
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
                "cod_amount": 10000,  # COD without partner status
                "authorized_max_fee_mmk": quote["maximum_fee_mmk"],
                "terms_accepted": True,
            },
        )

        assert response.status_code == 403
        assert "partner" in response.json()["detail"].lower()

    def test_approved_partner_can_create_cod_order(self, client, partner_headers, db_session):
        """Approved partners can create COD orders."""
        from tests.conftest import create_delivery_zone
        create_delivery_zone(db_session)
        quote_response = client.post(
            "/api/v1/quotes",
            headers=partner_headers,
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

        response = client.post(
            "/api/v1/orders",
            headers=partner_headers,
            json={
                "quote_id": quote["id"],
                "recipient_name": "Test",
                "recipient_phone": "09777777777",
                "pickup_address": "Test",
                "pickup_lat": 16.8409,
                "pickup_lng": 96.1735,
                "item_value": 50000,
                "cod_amount": 10000,  # COD allowed for partners
                "authorized_max_fee_mmk": quote["maximum_fee_mmk"],
                "terms_accepted": True,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert float(data["cod_amount"]) == 10000


class TestPartnerApproval:
    """Test partner approval process."""

    def test_admin_can_approve_partner(self, client, admin_headers, sender):
        """Admin can approve partner applications."""
        from tests.conftest import get_auth_headers
        sender_h = get_auth_headers(sender)
        apply_response = client.post(
            "/api/v1/partners/apply",
            headers=sender_h,
            json={
                "business_name": "Test Biz",
                "business_address": "Test Address",
                "contact_phone": "09123456781",
            },
        )
        application_id = apply_response.json()["id"]

        # Approve via admin endpoint (expects the application id, not the user id)
        response = client.patch(
            f"/api/v1/partners/{application_id}/approve",
            headers=admin_headers,
            json={},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"

    def test_admin_can_suspend_partner(self, client, admin_headers, partner):
        """Admin can suspend partners."""
        # Suspend is keyed on the partner's user id
        response = client.patch(
            f"/api/v1/partners/{partner.id}/suspend",
            headers=admin_headers,
            json={"suspended": True, "note": "Policy violation"},
        )

        assert response.status_code == 204
