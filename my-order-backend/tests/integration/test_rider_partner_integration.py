"""
Integration tests for rider and partner application flows (real API shape).

Rider routes (prefix /api/v1/riders):
- POST /apply                     - Rider submits application
- PATCH /{application_id}/approve - Admin approves
- PATCH /{application_id}/reject  - Admin rejects

Partner routes (prefix /api/v1/partners):
- POST /apply                       - Sender applies for partner status
- GET  /applications                - Admin lists applications
- PATCH /{application_id}/approve   - Admin approves
- PATCH /{application_id}/reject    - Admin rejects
"""
import pytest


class TestRiderApplication:
    """Test rider application process."""

    def test_rider_can_apply(self, client, db_session):
        """A rider without a profile can submit an application."""
        from tests.conftest import create_user, get_auth_headers
        from app.models.user import UserRole

        rider = create_user(db_session, phone="09333333399", role=UserRole.rider)
        headers = get_auth_headers(rider)

        response = client.post(
            "/api/v1/riders/apply",
            headers=headers,
            json={
                "nrc": "12/ABC(N)123456",
                "license_number": "LIC-12345",
                "vehicle_plate": "YGN-5678",
            },
        )

        assert response.status_code == 201, response.text
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
                "vehicle_plate": "YGN-5678",
            },
        )

        assert response.status_code == 403

    def test_cannot_apply_twice_while_pending(self, client, db_session):
        """Only one pending application allowed at a time."""
        from tests.conftest import create_user, get_auth_headers
        from app.models.user import UserRole

        rider = create_user(db_session, phone="09333333398", role=UserRole.rider)
        headers = get_auth_headers(rider)
        payload = {
            "nrc": "12/ABC(N)123456",
            "license_number": "LIC-12345",
            "vehicle_plate": "YGN-5678",
        }

        r1 = client.post("/api/v1/riders/apply", headers=headers, json=payload)
        assert r1.status_code == 201

        r2 = client.post("/api/v1/riders/apply", headers=headers, json=payload)
        assert r2.status_code == 400
        assert "pending" in r2.json()["detail"].lower()


class TestRiderReview:
    """Test admin review of rider applications."""

    def _create_pending_application(self, client, db_session, phone: str) -> dict:
        from tests.conftest import create_user, get_auth_headers
        from app.models.user import UserRole

        rider = create_user(db_session, phone=phone, role=UserRole.rider)
        headers = get_auth_headers(rider)

        response = client.post(
            "/api/v1/riders/apply",
            headers=headers,
            json={
                "nrc": "12/ABC(N)999999",
                "license_number": "LIC-999",
                "vehicle_plate": "YGN-9999",
            },
        )
        return response.json()

    def test_admin_can_approve_rider_application(self, client, admin_headers, db_session):
        application = self._create_pending_application(client, db_session, "09333333397")

        response = client.patch(
            f"/api/v1/riders/{application['id']}/approve",
            headers=admin_headers,
            json={"reviewer_notes": "Documents verified"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"

    def test_admin_approval_creates_rider_profile(self, client, admin_headers, db_session):
        """Approval should create an active RiderProfile."""
        from app.models.rider import RiderProfile

        application = self._create_pending_application(client, db_session, "09333333396")

        client.patch(
            f"/api/v1/riders/{application['id']}/approve",
            headers=admin_headers,
            json={},
        )

        profile = db_session.query(RiderProfile).filter(
            RiderProfile.user_id == application["user_id"]
        ).first()
        assert profile is not None
        assert profile.active_status is True

    def test_admin_can_reject_rider_application(self, client, admin_headers, db_session):
        application = self._create_pending_application(client, db_session, "09333333395")

        response = client.patch(
            f"/api/v1/riders/{application['id']}/reject",
            headers=admin_headers,
            json={"reviewer_notes": "Invalid license"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"

    def test_sender_cannot_approve_rider_application(self, client, sender_headers, db_session):
        application = self._create_pending_application(client, db_session, "09333333394")

        response = client.patch(
            f"/api/v1/riders/{application['id']}/approve",
            headers=sender_headers,
            json={},
        )

        assert response.status_code == 403


class TestPartnerApplication:
    """Test partner application process."""

    APPLY_PAYLOAD = {
        "business_name": "My Shop",
        "business_address": "123 Business St",
        "contact_phone": "09666666666",
    }

    def _apply_as(self, client, headers) -> dict:
        response = client.post("/api/v1/partners/apply", headers=headers, json=self.APPLY_PAYLOAD)
        assert response.status_code == 201, response.text
        return response.json()

    def test_sender_can_apply_as_partner(self, client, sender_headers):
        data = self._apply_as(client, sender_headers)
        assert data["status"] == "pending_review"

    def test_admin_can_list_applications(self, client, admin_headers, sender_headers):
        self._apply_as(client, sender_headers)

        response = client.get("/api/v1/partners/applications", headers=admin_headers)

        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 1

    def test_sender_cannot_list_applications(self, client, sender_headers):
        response = client.get("/api/v1/partners/applications", headers=sender_headers)

        assert response.status_code == 403

    def test_admin_can_approve_partner_application(self, client, admin_headers, sender_headers):
        application = self._apply_as(client, sender_headers)

        response = client.patch(
            f"/api/v1/partners/{application['id']}/approve",
            headers=admin_headers,
            json={"reviewer_notes": "Verified business"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "approved"

    def test_admin_can_reject_partner_application(self, client, admin_headers, sender_headers):
        application = self._apply_as(client, sender_headers)

        response = client.patch(
            f"/api/v1/partners/{application['id']}/reject",
            headers=admin_headers,
            json={"reviewer_notes": "Incomplete documents"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "rejected"


class TestCODRestrictions:
    """COD orders are only for approved partners."""

    def d2d_quote_payload(self):
        return {
            "delivery_mode": "door_to_door",
            "destination_city": "Yangon",
            "destination_township": "kamayut",
            "dropoff_address": "789 Destination St",
            "dropoff_lat": 16.8500,
            "dropoff_lng": 96.1800,
        }

    def test_non_partner_cannot_create_cod_order(self, client, sender_headers, db_session):
        """Regular senders cannot create COD orders."""
        from tests.conftest import create_delivery_zone

        create_delivery_zone(db_session)
        quote = client.post("/api/v1/quotes", headers=sender_headers, json=self.d2d_quote_payload()).json()

        response = client.post(
            "/api/v1/orders",
            headers=sender_headers,
            json={
                "quote_id": quote["id"],
                "recipient_name": "Daw Mya",
                "recipient_phone": "09777777777",
                "pickup_address": "123 Pickup St",
                "pickup_lat": 16.8409,
                "pickup_lng": 96.1735,
                "item_value": 50000,
                "cod_amount": 10000,  # COD without partner status
                "authorized_max_fee_mmk": float(quote["maximum_fee_mmk"]),
                "terms_accepted": True,
            },
        )

        assert response.status_code == 403
        assert "partner" in response.json()["detail"].lower()

    def test_approved_partner_can_create_cod_order(self, client, partner_headers, db_session):
        """Approved partners can create COD orders."""
        from tests.conftest import create_delivery_zone

        create_delivery_zone(db_session)
        quote = client.post("/api/v1/quotes", headers=partner_headers, json=self.d2d_quote_payload()).json()

        response = client.post(
            "/api/v1/orders",
            headers=partner_headers,
            json={
                "quote_id": quote["id"],
                "recipient_name": "Daw Mya",
                "recipient_phone": "09777777777",
                "pickup_address": "123 Pickup St",
                "pickup_lat": 16.8409,
                "pickup_lng": 96.1735,
                "item_value": 50000,
                "cod_amount": 10000,  # Partner COD allowed
                "authorized_max_fee_mmk": float(quote["maximum_fee_mmk"]),
                "terms_accepted": True,
            },
        )

        assert response.status_code == 201, response.text
