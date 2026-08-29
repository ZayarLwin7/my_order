"""
Integration tests for pricing and quote endpoints (real API shape).

Real routes:
- POST /api/v1/quotes                        - Create quote (sender or staff)
- GET  /api/v1/quotes/{id}                   - Get own quote
- POST /api/v1/admin/item-size-rates         - Admin creates rate
- GET  /api/v1/admin/item-size-rates         - Admin lists rates
"""
import pytest
from decimal import Decimal


# Payloads matching DeliveryQuoteCreate schema
D2D_QUOTE = {
    "delivery_mode": "door_to_door",
    "destination_city": "Yangon",
    "destination_township": "kamayut",
    "dropoff_address": "789 Destination St",
    "dropoff_lat": 16.8500,
    "dropoff_lng": 96.1800,
}

BUS_QUOTE = {
    "delivery_mode": "bus_terminal",
    "destination_town": "Taunggyi",
    "terminal_name": "Aung Mingalar",
    "bus_line": "Yangon-Taunggyi",
}


class TestDeliveryQuotes:
    """Test delivery quote generation."""

    def test_sender_can_get_door_to_door_quote(self, client, sender_headers, delivery_zone):
        """Sender can request door-to-door quote in an active zone."""
        response = client.post("/api/v1/quotes", headers=sender_headers, json=D2D_QUOTE)

        assert response.status_code == 201
        data = response.json()
        assert data["delivery_mode"] == "door_to_door"
        assert float(data["base_fee_mmk"]) == 3500
        assert float(data["zone_surcharge_mmk"]) == 500
        assert float(data["estimated_fee_mmk"]) == 4000  # base + surcharge, no discount
        assert data["fee_payer"] == "sender"
        assert "expires_at" in data

    def test_sender_can_get_bus_terminal_quote(self, client, sender_headers):
        """Sender can request bus-terminal quote without a delivery zone."""
        response = client.post("/api/v1/quotes", headers=sender_headers, json=BUS_QUOTE)

        assert response.status_code == 201
        data = response.json()
        assert data["delivery_mode"] == "bus_terminal"
        assert data["fee_payer"] == "sender"  # forced sender-pays for bus terminal
        assert data["terminal_name"] == "Aung Mingalar"
        assert float(data["zone_surcharge_mmk"]) == 0

    def test_staff_can_get_quote_for_walkin(self, client, staff_headers, delivery_zone):
        """Staff can request quotes on behalf of walk-in customers."""
        response = client.post("/api/v1/quotes", headers=staff_headers, json=D2D_QUOTE)

        assert response.status_code == 201
        assert response.json()["delivery_mode"] == "door_to_door"

    def test_rider_cannot_request_quote(self, client, rider_headers):
        """Riders cannot request quotes."""
        response = client.post(
            "/api/v1/quotes",
            headers=rider_headers,
            json={
                "delivery_mode": "bus_terminal",
                "destination_town": "Taunggyi",
                "terminal_name": "Aung Mingalar",
                "bus_line": "Yangon-Taunggyi",
            },
        )

        assert response.status_code == 403

    def test_d2d_quote_requires_active_zone(self, client, sender_headers):
        """Door-to-door quote fails if destination township is not an active zone."""
        response = client.post(
            "/api/v1/quotes",
            headers=sender_headers,
            json={**D2D_QUOTE, "destination_township": "nowhere"},
        )

        assert response.status_code == 400
        assert "delivery zone" in response.json()["detail"].lower()

    def test_d2d_quote_only_in_yangon_mandalay(self, client, sender_headers):
        """Door-to-door is restricted to Yangon/Mandalay cities."""
        response = client.post(
            "/api/v1/quotes",
            headers=sender_headers,
            json={**D2D_QUOTE, "destination_city": "Taunggyi"},
        )

        assert response.status_code == 400

    def test_d2d_quote_requires_all_fields(self, client, sender_headers, delivery_zone):
        """Missing drop-off fields fail validation."""
        payload = {k: v for k, v in D2D_QUOTE.items() if k != "dropoff_address"}
        response = client.post("/api/v1/quotes", headers=sender_headers, json=payload)

        assert response.status_code == 422

    def test_partner_discount_applied_to_quote(self, client, partner_headers, db_session, delivery_zone):
        """Active partner discount reduces the estimated fee."""
        from app.models.partner import PartnerProfile

        partner_profile = db_session.query(PartnerProfile).filter(
            PartnerProfile.user_id.isnot(None)
        ).first()
        partner_profile.delivery_discount_mmk = Decimal("1000")
        db_session.commit()

        response = client.post("/api/v1/quotes", headers=partner_headers, json=D2D_QUOTE)

        assert response.status_code == 201
        data = response.json()
        assert float(data["partner_discount_mmk"]) == 1000
        assert float(data["estimated_fee_mmk"]) == 3000  # 3500 base + 500 surcharge - 1000 discount

    def test_sender_can_get_own_quote(self, client, sender, sender_headers, delivery_zone):
        """Sender can retrieve their own quote by ID."""
        quote_response = client.post("/api/v1/quotes", headers=sender_headers, json=D2D_QUOTE)
        quote_id = quote_response.json()["id"]

        response = client.get(f"/api/v1/quotes/{quote_id}", headers=sender_headers)

        assert response.status_code == 200
        assert response.json()["id"] == quote_id


class TestItemSizeRates:
    """Test item size rate management."""

    def test_admin_can_create_item_size_rate(self, client, admin_headers):
        """Admin can create item size rates."""
        response = client.post(
            "/api/v1/admin/item-size-rates",
            headers=admin_headers,
            json={"name": "extra_large", "surcharge_mmk": 2000, "active": True},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "extra_large"
        assert float(data["surcharge_mmk"]) == 2000

    def test_duplicate_rate_name_rejected(self, client, admin_headers):
        """Duplicate item size names are rejected."""
        payload = {"name": "medium", "surcharge_mmk": 1000, "active": True}
        r1 = client.post("/api/v1/admin/item-size-rates", headers=admin_headers, json=payload)
        assert r1.status_code == 201

        r2 = client.post("/api/v1/admin/item-size-rates", headers=admin_headers, json=payload)
        assert r2.status_code == 400

    def test_sender_cannot_create_item_size_rate(self, client, sender_headers):
        """Senders cannot create item size rates."""
        response = client.post(
            "/api/v1/admin/item-size-rates",
            headers=sender_headers,
            json={"name": "hack", "surcharge_mmk": 0, "active": True},
        )

        assert response.status_code == 403

    def test_admin_can_list_item_size_rates(self, client, admin_headers):
        """Admin can list all item size rates."""
        client.post(
            "/api/v1/admin/item-size-rates",
            headers=admin_headers,
            json={"name": "small", "surcharge_mmk": 0, "active": True},
        )
        client.post(
            "/api/v1/admin/item-size-rates",
            headers=admin_headers,
            json={"name": "large", "surcharge_mmk": 1500, "active": True},
        )

        response = client.get("/api/v1/admin/item-size-rates", headers=admin_headers)

        assert response.status_code == 200
        names = [r["name"] for r in response.json()]
        assert "small" in names
        assert "large" in names

    def test_rider_cannot_manage_item_size_rates(self, client, rider_headers):
        """Riders cannot manage item size rates."""
        response = client.post(
            "/api/v1/admin/item-size-rates",
            headers=rider_headers,
            json={"name": "test", "surcharge_mmk": 100, "active": True},
        )

        assert response.status_code == 403


class TestDeliveryZones:
    """Test delivery zone management (admin)."""

    def test_admin_can_create_zone(self, client, admin_headers):
        """Admin can create delivery zones for Yangon/Mandalay only."""
        response = client.post(
            "/api/v1/admin/delivery-zones",
            headers=admin_headers,
            json={"city": "Mandalay", "township": "chanayethazan", "surcharge_mmk": 800, "active": True},
        )

        assert response.status_code == 201
        assert float(response.json()["surcharge_mmk"]) == 800

    def test_zone_outside_yangon_mandalay_rejected(self, client, admin_headers):
        response = client.post(
            "/api/v1/admin/delivery-zones",
            headers=admin_headers,
            json={"city": "Taunggyi", "township": "center", "surcharge_mmk": 500, "active": True},
        )

        assert response.status_code == 400

    def test_duplicate_zone_rejected(self, client, admin_headers):
        payload = {"city": "Yangon", "township": "hlaing", "surcharge_mmk": 300, "active": True}
        r1 = client.post("/api/v1/admin/delivery-zones", headers=admin_headers, json=payload)
        assert r1.status_code == 201

        r2 = client.post("/api/v1/admin/delivery-zones", headers=admin_headers, json=payload)
        assert r2.status_code == 400

    def test_sender_cannot_access_admin_zones(self, client, sender_headers):
        response = client.get("/api/v1/admin/delivery-zones", headers=sender_headers)

        assert response.status_code == 403
