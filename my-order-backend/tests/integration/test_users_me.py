"""
Integration tests for GET /api/v1/users/me (partner status included).
"""
import pytest


class TestUsersMe:
    def test_regular_sender_has_no_partner_status(self, client, sender, sender_headers):
        response = client.get("/api/v1/users/me", headers=sender_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "sender"
        assert data["partner_status"] == "none"
        assert data["is_active_partner"] is False

    def test_pending_applicant_reports_pending_review(self, client, sender, sender_headers):
        client.post(
            "/api/v1/partners/apply",
            headers=sender_headers,
            json={
                "business_name": "My Shop",
                "business_address": "123 St",
                "contact_phone": "09666666666",
            },
        )

        response = client.get("/api/v1/users/me", headers=sender_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["partner_status"] == "pending_review"
        assert data["partner_business_name"] == "My Shop"

    def test_approved_partner_is_active(self, client, partner, partner_headers):
        response = client.get("/api/v1/users/me", headers=partner_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["partner_status"] == "approved"
        assert data["is_active_partner"] is True
        assert data["partner_business_name"] == "Test Business"

    def test_rider_and_staff_have_no_partner_fields(self, client, rider_headers, staff_headers):
        r_rider = client.get("/api/v1/users/me", headers=rider_headers)
        r_staff = client.get("/api/v1/users/me", headers=staff_headers)

        assert r_rider.status_code == 200
        assert r_rider.json()["role"] == "rider"
        assert r_rider.json()["partner_status"] == "none"
        assert r_staff.status_code == 200
        assert r_staff.json()["role"] == "staff"

    def test_new_rider_reports_none_then_pending(self, client, db_session):
        """Fresh rider -> none; after applying -> pending_review."""
        from tests.conftest import create_user, get_auth_headers
        from app.models.user import UserRole

        rider = create_user(db_session, phone="09333333390", role=UserRole.rider)
        headers = get_auth_headers(rider)

        me = client.get("/api/v1/users/me", headers=headers).json()
        assert me["rider_status"] == "none"
        assert me["is_active_rider"] is False

        client.post(
            "/api/v1/riders/apply",
            headers=headers,
            json={
                "nrc": "12/ABC(N)000001",
                "license_number": "LIC-900",
                "vehicle_plate": "YGN-9000",
            },
        )

        me = client.get("/api/v1/users/me", headers=headers).json()
        assert me["rider_status"] == "pending_review"

    def test_approved_rider_is_active(self, client, rider_headers):
        """Fixture riders have approved profiles and are active."""
        me = client.get("/api/v1/users/me", headers=rider_headers).json()
        assert me["rider_status"] == "approved"
        assert me["is_active_rider"] is True

    def test_requires_authentication(self, client):
        response = client.get("/api/v1/users/me")

        assert response.status_code == 401
