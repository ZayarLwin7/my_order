"""
Integration tests for the admin-web MVP endpoints:

- GET /riders/applications        - admin lists rider applications
- GET /riders/active              - admin lists assignable riders
- GET /orders?status=pending      - admin lists orders
"""
import pytest


class TestRiderApplicationList:
    def _create_pending_application(self, client, db_session, phone: str) -> dict:
        from tests.conftest import create_user, get_auth_headers
        from app.models.user import UserRole

        rider = create_user(db_session, phone=phone, role=UserRole.rider)
        client.post(
            "/api/v1/riders/apply",
            headers=get_auth_headers(rider),
            json={
                "nrc": "12/ABC(N)700001",
                "license_number": "LIC-700",
                "vehicle_plate": "YGN-7000",
            },
        )
        return {"user_id": str(rider.id)}

    def test_admin_can_list_pending_applications(self, client, admin_headers, db_session):
        self._create_pending_application(client, db_session, "09333333311")
        self._create_pending_application(client, db_session, "09333333312")

        response = client.get("/api/v1/riders/applications", headers=admin_headers)

        assert response.status_code == 200
        apps = response.json()
        assert isinstance(apps, list)
        assert len(apps) >= 2
        assert all(a["status"] == "pending_review" for a in apps)

    def test_admin_can_filter_applications_by_status(self, client, admin_headers, db_session):
        from tests.conftest import create_user, get_auth_headers
        from app.models.user import UserRole

        rider = create_user(db_session, phone="09333333313", role=UserRole.rider)
        app = client.post(
            "/api/v1/riders/apply",
            headers=get_auth_headers(rider),
            json={"nrc": "12/ABC(N)700002", "license_number": "LIC-701", "vehicle_plate": "YGN-7001"},
        ).json()

        client.patch(f"/api/v1/riders/{app['id']}/approve", headers=admin_headers, json={})

        pending = client.get("/api/v1/riders/applications", headers=admin_headers).json()
        approved = client.get("/api/v1/riders/applications?status=approved", headers=admin_headers).json()

        assert app["id"] not in [a["id"] for a in pending]
        assert app["id"] in [a["id"] for a in approved]

    def test_sender_cannot_list_applications(self, client, sender_headers):
        response = client.get("/api/v1/riders/applications", headers=sender_headers)
        assert response.status_code == 403


class TestActiveRidersList:
    def test_admin_gets_only_active_riders(self, client, admin_headers, rider, db_session):
        """Approved+active fixture riders appear; pending/inactive do not."""
        from tests.conftest import create_user, get_auth_headers
        from app.models.user import UserRole
        from app.models.rider import RiderProfile, ApplicationStatus

        # Inactive rider (no approved profile)
        create_user(db_session, phone="09333333321", role=UserRole.rider)

        # Suspended rider
        from tests.conftest import create_rider
        suspended = create_rider(db_session, phone="09333333322")
        p = db_session.query(RiderProfile).filter(RiderProfile.user_id == suspended.id).first()
        p.suspended = True
        db_session.commit()

        response = client.get("/api/v1/riders/active", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        ids = {r["user_id"] for r in data}
        assert str(rider.id) in ids  # fixture rider is active
        assert suspended.id not in ids

    def test_sender_cannot_list_active_riders(self, client, sender_headers):
        response = client.get("/api/v1/riders/active", headers=sender_headers)
        assert response.status_code == 403


class TestOrderList:
    def test_admin_can_list_pending_orders(self, client, sender_headers, admin_headers, db_session):
        """Create an order, then admin sees it in the pending queue."""
        from tests.conftest import create_delivery_zone

        create_delivery_zone(db_session)
        quote = client.post(
            "/api/v1/quotes",
            headers=sender_headers,
            json={
                "delivery_mode": "door_to_door",
                "destination_city": "Yangon",
                "destination_township": "kamayut",
                "dropoff_address": "789 Test St",
                "dropoff_lat": 16.85,
                "dropoff_lng": 96.18,
            },
        ).json()

        order_resp = client.post(
            "/api/v1/orders",
            headers=sender_headers,
            json={
                "quote_id": quote["id"],
                "recipient_name": "Daw Mya",
                "recipient_phone": "09777777771",
                "pickup_address": "123 Pickup",
                "pickup_lat": 16.84,
                "pickup_lng": 96.17,
                "item_value": 50000,
                "cod_amount": 0,
                "authorized_max_fee_mmk": float(quote["maximum_fee_mmk"]),
                "terms_accepted": True,
            },
        )
        assert order_resp.status_code == 201
        order_id = order_resp.json()["id"]

        response = client.get("/api/v1/orders?status=pending", headers=admin_headers)

        assert response.status_code == 200
        orders = response.json()
        assert order_id in [o["id"] for o in orders]

    def test_sender_cannot_list_all_orders(self, client, sender_headers):
        response = client.get("/api/v1/orders", headers=sender_headers)
        assert response.status_code == 403

    def test_admin_full_queue_and_assign(self, client, sender_headers, admin_headers, rider, db_session):
        """Admin lists pending, assigns, then order leaves the queue."""
        from tests.conftest import create_delivery_zone

        create_delivery_zone(db_session)
        quote = client.post(
            "/api/v1/quotes",
            headers=sender_headers,
            json={
                "delivery_mode": "door_to_door",
                "destination_city": "Yangon",
                "destination_township": "kamayut",
                "dropoff_address": "789 Test St",
                "dropoff_lat": 16.85,
                "dropoff_lng": 96.18,
            },
        ).json()

        order = client.post(
            "/api/v1/orders",
            headers=sender_headers,
            json={
                "quote_id": quote["id"],
                "recipient_name": "Daw Mya",
                "recipient_phone": "09777777772",
                "pickup_address": "123 Pickup",
                "pickup_lat": 16.84,
                "pickup_lng": 96.17,
                "item_value": 50000,
                "cod_amount": 0,
                "authorized_max_fee_mmk": float(quote["maximum_fee_mmk"]),
                "terms_accepted": True,
            },
        ).json()
        order_id = order["id"]

        assign = client.patch(
            f"/api/v1/orders/{order_id}/assign",
            headers=admin_headers,
            json={"rider_id": str(rider.id)},
        )
        assert assign.status_code == 200

        remaining = client.get("/api/v1/orders?status=pending", headers=admin_headers).json()
        assert order_id not in [o["id"] for o in remaining]
