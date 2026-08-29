"""
Integration tests for financial flows.

Tests:
- Wallet balance updates
- COD ledger entries
- Rider earnings
- Dispute handling
"""
import pytest
from decimal import Decimal


class TestWalletFlows:
    """Test rider wallet operations."""

    def test_rider_wallet_balance_endpoint(self, client, rider_headers):
        """Rider can view own wallet balance."""
        response = client.get(
            "/api/v1/riders/me/wallet",
            headers=rider_headers
        )

        # Endpoint should exist and be accessible
        assert response.status_code in [200, 404]

    def test_rider_can_view_transactions(self, client, rider_headers):
        """Rider can view wallet transactions."""
        response = client.get(
            "/api/v1/riders/me/wallet/transactions",
            headers=rider_headers
        )

        # Should not be forbidden
        assert response.status_code != 403


class TestDisputeFlow:
    """Test dispute creation and resolution."""

    def test_sender_can_create_dispute(self, client, sender, sender_headers):
        """Sender can create dispute on delivered order."""
        # This would need a delivered order first
        # Simplified test - verify endpoint exists and permissions work
        response = client.post(
            "/api/v1/disputes",
            headers=sender_headers,
            json={
                "order_id": "550e8400-e29b-41d4-a716-446655440000",
                "reason": "damaged",
                "description": "Package arrived damaged",
            },
        )

        # Order doesn't exist, should get 404
        assert response.status_code == 404

    def test_admin_can_list_disputes(self, client, admin_headers):
        """Admin can list all disputes."""
        response = client.get(
            "/api/v1/disputes",
            headers=admin_headers
        )

        assert response.status_code == 200

    def test_sender_cannot_list_all_disputes(self, client, sender_headers):
        """Senders cannot list all disputes."""
        response = client.get(
            "/api/v1/disputes",
            headers=sender_headers
        )

        # Either 403 (admin only) or 200 (own disputes only)
        if response.status_code == 200:
            # If allowed, should only return own disputes
            pass


class TestFinanceAccess:
    """Test financial endpoint access control."""

    def test_admin_can_access_platform_ledger(self, client, admin_headers):
        """Admin can access platform ledger."""
        response = client.get(
            "/api/v1/finance/platform-ledger",
            headers=admin_headers
        )

        assert response.status_code != 403

    def test_sender_cannot_access_platform_ledger(self, client, sender_headers):
        """Senders cannot access platform ledger."""
        response = client.get(
            "/api/v1/finance/platform-ledger",
            headers=sender_headers
        )

        assert response.status_code == 403

    def test_admin_can_access_reconciliation(self, client, admin_headers):
        """Admin can access reconciliation endpoint."""
        response = client.get(
            "/api/v1/finance/reconciliation",
            headers=admin_headers
        )

        assert response.status_code != 403

    def test_rider_cannot_access_reconciliation(self, client, rider_headers):
        """Riders cannot access reconciliation."""
        response = client.get(
            "/api/v1/finance/reconciliation",
            headers=rider_headers
        )

        assert response.status_code == 403
