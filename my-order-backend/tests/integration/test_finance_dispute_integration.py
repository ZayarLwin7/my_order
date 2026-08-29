"""
Integration tests for finance and dispute flows (real API shape).

Finance routes (prefix /api/v1/finance, admin only):
- GET /platform-ledger
- GET /reconciliation

Dispute routes (prefix /api/v1/disputes):
- POST ""                      - Sender files dispute on own completed order
- GET  /{dispute_id}           - Admin or filer views dispute
- PATCH /{dispute_id}/resolve  - Admin resolves
"""
import pytest
from datetime import date


def _any_admin_id(db_session):
    """Find any admin user ID for rate creation, or create one."""
    from tests.conftest import create_admin
    from app.models.user import User, UserRole

    admin = db_session.query(User).filter(User.role == UserRole.admin).first()
    if not admin:
        import uuid
        # Create a standalone admin with a unique phone for this purpose
        admin = create_admin(db_session, phone=f"097{uuid.uuid4().hex[:8]}")
    return str(admin.id)


def d2d_quote_payload():
    return {
        "delivery_mode": "door_to_door",
        "destination_city": "Yangon",
        "destination_township": "kamayut",
        "dropoff_address": "789 Destination St",
        "dropoff_lat": 16.8500,
        "dropoff_lng": 96.1800,
    }


class TestFinanceAccess:
    """Test financial endpoint access control."""

    def test_admin_can_access_platform_ledger(self, client, admin_headers):
        response = client.get("/api/v1/finance/platform-ledger", headers=admin_headers)

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_sender_cannot_access_platform_ledger(self, client, sender_headers):
        response = client.get("/api/v1/finance/platform-ledger", headers=sender_headers)

        assert response.status_code == 403

    def test_admin_can_access_reconciliation(self, client, admin_headers):
        response = client.get("/api/v1/finance/reconciliation", headers=admin_headers)

        assert response.status_code == 200

    def test_rider_cannot_access_reconciliation(self, client, rider_headers):
        response = client.get("/api/v1/finance/reconciliation", headers=rider_headers)

        assert response.status_code == 403

    def test_unauthenticated_cannot_access_finance(self, client):
        response = client.get("/api/v1/finance/platform-ledger")

        assert response.status_code == 401


class TestDisputeFlow:
    """Test the full dispute lifecycle with a real delivered order."""

    def _create_delivered_order(self, client, sender_headers, sender, rider,
                                rider_headers, admin_headers, db_session) -> dict:
        """Helper: create a fully delivered order. Returns order dict."""
        from tests.conftest import create_delivery_zone
        from app.models.rider_earnings import RiderCompensationRate

        create_delivery_zone(db_session)
        client.post(
            "/api/v1/admin/item-size-rates",
            headers=admin_headers,
            json={"name": "small", "surcharge_mmk": 0, "active": True},
        )
        # Delivery completion requires an active rider compensation rate
        # (backend credits rider earnings on delivered/dropped_at_terminal).
        existing_rate = db_session.query(RiderCompensationRate).filter(
            RiderCompensationRate.effective_from <= date.today()
        ).first()
        if not existing_rate:
            db_session.add(RiderCompensationRate(
                per_completed_way_mmk=1000,
                effective_from=date.today(),
                created_by_user_id=_any_admin_id(db_session),
            ))
            db_session.commit()

        quote = client.post("/api/v1/quotes", headers=sender_headers, json=d2d_quote_payload()).json()

        order_response = client.post(
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
                "cod_amount": 0,
                "authorized_max_fee_mmk": float(quote["maximum_fee_mmk"]),
                "terms_accepted": True,
            },
        )
        order = order_response.json()

        client.patch(f"/api/v1/orders/{order['id']}/assign", headers=admin_headers,
                     json={"rider_id": str(rider.id)})
        client.patch(f"/api/v1/orders/{order['id']}/verify-item-size", headers=rider_headers,
                     json={"item_size": "small"})
        client.patch(f"/api/v1/orders/{order['id']}/confirm-final-fee", headers=sender_headers)
        client.patch(f"/api/v1/orders/{order['id']}/status", headers=rider_headers,
                     json={"status": "picked_up"})
        r = client.patch(f"/api/v1/orders/{order['id']}/status", headers=rider_headers,
                         json={"status": "delivered"})
        assert r.status_code == 200
        return order

    def test_sender_can_file_dispute_on_delivered_order(
        self, client, sender_headers, sender, rider, rider_headers, admin_headers, db_session
    ):
        order = self._create_delivered_order(
            client, sender_headers, sender, rider, rider_headers, admin_headers, db_session
        )

        response = client.post(
            "/api/v1/disputes",
            headers=sender_headers,
            json={
                "order_id": order["id"],
                "reason": "damaged",
                "description": "Package arrived damaged",
            },
        )

        assert response.status_code == 201, response.text
        data = response.json()
        assert data["status"] == "open"
        assert data["reason"] == "damaged"

    def test_dispute_changes_order_status(
        self, client, sender_headers, sender, rider, rider_headers, admin_headers, db_session
    ):
        """Filing a dispute sets the order to 'disputed'."""
        order = self._create_delivered_order(
            client, sender_headers, sender, rider, rider_headers, admin_headers, db_session
        )

        client.post(
            "/api/v1/disputes",
            headers=sender_headers,
            json={"order_id": order["id"], "reason": "missing"},
        )

        # Verify via tracking endpoint
        tracking = client.get(f"/api/v1/tracking/{order['id']}", headers=sender_headers)
        assert tracking.status_code == 200
        statuses = [m["status"] for m in tracking.json()["milestones"]]
        assert "disputed" in statuses

    def test_cannot_file_second_dispute_while_open(
        self, client, sender_headers, sender, rider, rider_headers, admin_headers, db_session
    ):
        order = self._create_delivered_order(
            client, sender_headers, sender, rider, rider_headers, admin_headers, db_session
        )

        r1 = client.post(
            "/api/v1/disputes",
            headers=sender_headers,
            json={"order_id": order["id"], "reason": "damaged"},
        )
        assert r1.status_code == 201

        r2 = client.post(
            "/api/v1/disputes",
            headers=sender_headers,
            json={"order_id": order["id"], "reason": "missing"},
        )
        # Order is now in 'disputed' status, so the completion-status guard fires
        # first; either way a second open dispute must be rejected.
        assert r2.status_code == 400

    def test_non_owner_cannot_file_dispute(
        self, client, sender_headers, sender, rider, rider_headers, admin_headers, db_session
    ):
        """A different sender cannot dispute someone else's order."""
        from tests.conftest import create_sender, get_auth_headers

        order = self._create_delivered_order(
            client, sender_headers, sender, rider, rider_headers, admin_headers, db_session
        )

        other = create_sender(db_session, phone="09999999992")
        response = client.post(
            "/api/v1/disputes",
            headers=get_auth_headers(other),
            json={"order_id": order["id"], "reason": "damaged"},
        )

        assert response.status_code == 403

    def test_admin_can_resolve_dispute_with_platform_refund(
        self, client, sender_headers, sender, rider, rider_headers, admin_headers, db_session
    ):
        """Full refund funded by platform resolves the dispute."""
        order = self._create_delivered_order(
            client, sender_headers, sender, rider, rider_headers, admin_headers, db_session
        )

        dispute = client.post(
            "/api/v1/disputes",
            headers=sender_headers,
            json={"order_id": order["id"], "reason": "damaged"},
        ).json()

        response = client.patch(
            f"/api/v1/disputes/{dispute['id']}/resolve",
            headers=admin_headers,
            json={
                "resolution_type": "full_refund",
                "resolved_amount": 50000,
                "refund_payer": "platform",
                "reviewer_notes": "Verified damage claim",
            },
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "resolved"
        assert data["resolution_type"] == "full_refund"
        assert data["resolved_at"] is not None

    def test_resolve_requires_amount_for_refund(
        self, client, sender_headers, sender, rider, rider_headers, admin_headers, db_session
    ):
        order = self._create_delivered_order(
            client, sender_headers, sender, rider, rider_headers, admin_headers, db_session
        )

        dispute = client.post(
            "/api/v1/disputes",
            headers=sender_headers,
            json={"order_id": order["id"], "reason": "damaged"},
        ).json()

        response = client.patch(
            f"/api/v1/disputes/{dispute['id']}/resolve",
            headers=admin_headers,
            json={"resolution_type": "full_refund"},  # missing resolved_amount
        )

        assert response.status_code == 400

    def test_rider_wallet_adjustment_resolution(
        self, client, sender_headers, sender, rider, rider_headers, admin_headers, db_session
    ):
        """Wallet adjustment credits/debits the rider's wallet."""
        order = self._create_delivered_order(
            client, sender_headers, sender, rider, rider_headers, admin_headers, db_session
        )

        dispute = client.post(
            "/api/v1/disputes",
            headers=sender_headers,
            json={"order_id": order["id"], "reason": "other"},
        ).json()

        response = client.patch(
            f"/api/v1/disputes/{dispute['id']}/resolve",
            headers=admin_headers,
            json={
                "resolution_type": "wallet_adjustment",
                "resolved_amount": -2000,  # debit rider
                "reviewer_notes": "Fee overcharge correction",
            },
        )

        assert response.status_code == 200
        assert response.json()["resolution_type"] == "wallet_adjustment"

    def test_admin_can_view_any_dispute(
        self, client, sender_headers, sender, rider, rider_headers, admin_headers, db_session
    ):
        order = self._create_delivered_order(
            client, sender_headers, sender, rider, rider_headers, admin_headers, db_session
        )

        dispute = client.post(
            "/api/v1/disputes",
            headers=sender_headers,
            json={"order_id": order["id"], "reason": "damaged"},
        ).json()

        response = client.get(f"/api/v1/disputes/{dispute['id']}", headers=admin_headers)

        assert response.status_code == 200

    def test_other_user_cannot_view_dispute(
        self, client, sender_headers, sender, rider, rider_headers, admin_headers, db_session
    ):
        from tests.conftest import create_sender, get_auth_headers

        order = self._create_delivered_order(
            client, sender_headers, sender, rider, rider_headers, admin_headers, db_session
        )

        dispute = client.post(
            "/api/v1/disputes",
            headers=sender_headers,
            json={"order_id": order["id"], "reason": "damaged"},
        ).json()

        other = create_sender(db_session, phone="09999999993")
        response = client.get(f"/api/v1/disputes/{dispute['id']}", headers=get_auth_headers(other))

        assert response.status_code == 403


class TestCODFinancialFlow:
    """Test that COD orders generate proper ledger entries."""

    def test_cod_order_delivery_creates_partner_credit(
        self, client, partner_headers, partner, rider, rider_headers, admin_headers, db_session
    ):
        """Delivering a COD order creates an on-hold partner credit and rider wallet collection."""
        from tests.conftest import create_delivery_zone
        from app.models.partner import PartnerLedgerEntry, PartnerLedgerEntryType, PartnerLedgerEntryStatus
        from app.models.wallet import WalletTransaction, TransactionType
        from app.models.rider import RiderProfile
        from app.models.rider_earnings import RiderCompensationRate

        create_delivery_zone(db_session)

        # Need rider compensation rate for delivery completion
        existing_rate = db_session.query(RiderCompensationRate).filter(
            RiderCompensationRate.effective_from <= date.today()
        ).first()
        if not existing_rate:
            db_session.add(RiderCompensationRate(
                per_completed_way_mmk=1000,
                effective_from=date.today(),
                created_by_user_id=_any_admin_id(db_session),
            ))
            db_session.commit()

        quote = client.post("/api/v1/quotes", headers=partner_headers, json=d2d_quote_payload()).json()

        order_response = client.post(
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
                "cod_amount": 20000,
                "authorized_max_fee_mmk": float(quote["maximum_fee_mmk"]),
                "terms_accepted": True,
            },
        )
        order = order_response.json()
        order_id = order["id"]

        client.patch(f"/api/v1/orders/{order_id}/assign", headers=admin_headers,
                     json={"rider_id": str(rider.id)})

        # Create small rate (no surcharge) and verify item size
        client.post(
            "/api/v1/admin/item-size-rates",
            headers=admin_headers,
            json={"name": "small", "surcharge_mmk": 0, "active": True},
        )
        r = client.patch(f"/api/v1/orders/{order_id}/verify-item-size", headers=rider_headers,
                         json={"item_size": "small"})
        assert r.status_code == 200, r.text
        # Fee equals estimate + 0 surcharge → auto-confirmed, but confirm anyway if needed
        client.patch(f"/api/v1/orders/{order_id}/confirm-final-fee", headers=partner_headers)

        r = client.patch(f"/api/v1/orders/{order_id}/status", headers=rider_headers,
                         json={"status": "picked_up"})
        assert r.status_code == 200

        r = client.patch(f"/api/v1/orders/{order_id}/status", headers=rider_headers,
                         json={"status": "delivered"})
        assert r.status_code == 200

        # Verify partner credit entry created (on hold during dispute window)
        credit = db_session.query(PartnerLedgerEntry).filter(
            PartnerLedgerEntry.order_id == order_id,
            PartnerLedgerEntry.type == PartnerLedgerEntryType.cod_credit,
        ).first()
        assert credit is not None
        assert float(credit.amount) == 20000
        assert credit.status == PartnerLedgerEntryStatus.on_hold

        # Verify rider wallet transaction for COD collection
        wallet_tx = db_session.query(WalletTransaction).filter(
            WalletTransaction.order_id == order_id,
            WalletTransaction.type == TransactionType.collection,
        ).first()
        assert wallet_tx is not None
        assert float(wallet_tx.amount) == 20000

        # Verify rider profile balance updated
        profile = db_session.query(RiderProfile).filter(RiderProfile.user_id == rider.id).first()
        assert float(profile.wallet_balance) == 20000
