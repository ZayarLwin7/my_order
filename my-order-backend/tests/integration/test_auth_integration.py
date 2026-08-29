"""
Integration tests for authentication endpoints.

Tests:
- User registration (sender, rider)
- Login flow
- Token validation
- Permission boundaries
"""
import pytest


class TestRegistration:
    """Test user registration flows."""

    def test_sender_can_register(self, client):
        """Sender registration should succeed."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "New Sender",
                "phone": "09777777777",
                "password": "securepassword123",
                "role": "sender"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Sender"
        assert data["phone"] == "09777777777"
        assert data["role"] == "sender"
        assert "id" in data

    def test_rider_can_register(self, client):
        """Rider registration should succeed."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "New Rider",
                "phone": "09888888888",
                "password": "securepassword123",
                "role": "rider"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "rider"

    def test_cannot_register_as_admin(self, client):
        """Public registration should reject admin role (validation error)."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "Hacker",
                "phone": "09999999999",
                "password": "securepassword123",
                "role": "admin"
            }
        )

        # PublicRegistrationRole enum only allows sender/rider -> Pydantic 422
        assert response.status_code == 422

    def test_cannot_register_as_staff(self, client):
        """Public registration should reject staff role."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "Hacker",
                "phone": "09999999998",
                "password": "securepassword123",
                "role": "staff"
            }
        )

        assert response.status_code == 422

    def test_duplicate_phone_rejected(self, client, sender):
        """Cannot register with existing phone number."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "Duplicate",
                "phone": sender.phone,
                "password": "securepassword123",
                "role": "sender"
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_short_password_rejected(self, client):
        """Password must be at least 12 characters."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "Test",
                "phone": "09111111119",
                "password": "short",
                "role": "sender"
            }
        )

        assert response.status_code == 422


class TestLogin:
    """Test login and authentication flows."""

    def test_login_success(self, client, sender):
        """Login with correct credentials should succeed."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "phone": sender.phone,
                "password": "testpassword123"  # From conftest factory
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, sender):
        """Login with wrong password should fail."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "phone": sender.phone,
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Login with non-existent user should fail."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "phone": "09000000000",
                "password": "anypassword123"
            }
        )

        assert response.status_code == 401

    def test_token_works_for_protected_route(self, client, sender_headers):
        """Valid token should access protected routes."""
        response = client.get(
            "/api/v1/pricing/quotes",
            headers=sender_headers
        )

        # Should not get 401 unauthorized
        assert response.status_code != 401

    def test_no_token_rejected(self, client):
        """Protected routes should reject requests without token."""
        response = client.post(
            "/api/v1/orders",
            json={}
        )

        assert response.status_code == 401


class TestRateLimiting:
    """Test rate limiting on auth endpoints."""

    def test_rate_limit_on_login(self, client):
        """Should rate limit excessive login attempts."""
        # Make 11 failed login attempts (limit is 10 per minute)
        for i in range(11):
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "phone": "09000000001",
                    "password": "wrong"
                }
            )

            if i < 10:
                assert response.status_code == 401  # Invalid credentials
            else:
                assert response.status_code == 429  # Rate limited
                assert "too many" in response.json()["detail"].lower()

    def test_rate_limit_on_register(self, client):
        """Should rate limit excessive registration attempts."""
        for i in range(11):
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "name": f"Test{i}",
                    "phone": f"0911111111{i}",
                    "password": "testpassword123",
                    "role": "sender"
                }
            )

            if i < 10:
                assert response.status_code in [201, 422]  # Success or validation
            else:
                assert response.status_code == 429  # Rate limited
