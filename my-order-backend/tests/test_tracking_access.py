from types import SimpleNamespace
import uuid

import pytest
from fastapi import HTTPException

from app.models.order import DeliveryMode, Order, OrderStatus, OrderTrackingLog
from app.models.user import UserRole
from app.routers.tracking import get_tracking


class TrackingQuery:
    def __init__(self, record, records=None):
        self.record = record
        self.records = records or []

    def filter(self, *args):
        return self

    def order_by(self, *args):
        return self

    def first(self):
        return self.record

    def all(self):
        return self.records


class TrackingDb:
    def __init__(self, order):
        self.order = order

    def query(self, model):
        if model is Order:
            return TrackingQuery(self.order)
        if model is OrderTrackingLog:
            return TrackingQuery(None, [])
        raise AssertionError(f"Unexpected query model: {model}")


def make_order():
    return SimpleNamespace(
        id=uuid.uuid4(),
        sender_id=uuid.uuid4(),
        rider_id=uuid.uuid4(),
        delivery_mode=DeliveryMode.door_to_door,
        recipient_name="May Su",
        status=OrderStatus.assigned,
        terminal_name=None,
        bus_line=None,
    )


def user(user_id, role):
    return SimpleNamespace(id=user_id, role=role)


def test_order_sender_can_view_tracking():
    order = make_order()

    tracking = get_tracking(order.id, TrackingDb(order), user(order.sender_id, UserRole.sender))

    assert tracking.order_id == order.id
    assert tracking.current_status == OrderStatus.assigned


def test_assigned_rider_can_view_tracking():
    order = make_order()

    tracking = get_tracking(order.id, TrackingDb(order), user(order.rider_id, UserRole.rider))

    assert tracking.order_id == order.id


def test_admin_can_view_tracking():
    order = make_order()

    tracking = get_tracking(order.id, TrackingDb(order), user(uuid.uuid4(), UserRole.admin))

    assert tracking.order_id == order.id


def test_unrelated_sender_cannot_view_tracking():
    order = make_order()

    with pytest.raises(HTTPException) as error:
        get_tracking(order.id, TrackingDb(order), user(uuid.uuid4(), UserRole.sender))

    assert error.value.status_code == 403
    assert error.value.detail == "Not authorized to view this order's tracking"
