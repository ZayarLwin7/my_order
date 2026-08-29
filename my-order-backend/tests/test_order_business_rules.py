from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.order import OrderStatus
from app.routers.orders import ALLOWED_TRANSITIONS
from app.schemas.order import OrderCreate


def test_rider_state_machine_allows_only_forward_operational_transitions():
    assert ALLOWED_TRANSITIONS[OrderStatus.assigned] == {OrderStatus.picked_up}
    assert ALLOWED_TRANSITIONS[OrderStatus.picked_up] == {
        OrderStatus.delivered,
        OrderStatus.dropped_at_terminal,
        OrderStatus.delivery_failed,
    }
    assert OrderStatus.delivered not in ALLOWED_TRANSITIONS[OrderStatus.assigned]
    assert OrderStatus.cancelled not in ALLOWED_TRANSITIONS[OrderStatus.picked_up]


def test_order_create_requires_quote_and_sender_fee_authorization():
    with pytest.raises(ValidationError) as error:
        OrderCreate(
            recipient_name="May Su",
            recipient_phone="09123456789",
            pickup_address="Bahan",
            pickup_lat=16.81,
            pickup_lng=96.15,
            item_value=Decimal("50000"),
            cod_amount=Decimal("0"),
            terms_accepted=True,
        )

    missing = {item["loc"][-1] for item in error.value.errors()}
    assert {"quote_id", "authorized_max_fee_mmk"}.issubset(missing)


def test_order_create_rejects_negative_authorized_max_fee():
    with pytest.raises(ValidationError, match="greater than or equal to 0"):
        OrderCreate(
            quote_id="00000000-0000-0000-0000-000000000000",
            recipient_name="May Su",
            recipient_phone="09123456789",
            pickup_address="Bahan",
            pickup_lat=16.81,
            pickup_lng=96.15,
            item_value=Decimal("50000"),
            authorized_max_fee_mmk=Decimal("-1"),
            terms_accepted=True,
        )


def test_completion_states_are_the_only_states_that_trigger_financial_posting():
    completion_states = {OrderStatus.delivered, OrderStatus.dropped_at_terminal}

    assert OrderStatus.picked_up not in completion_states
    assert OrderStatus.delivery_failed not in completion_states
    assert OrderStatus.cancelled not in completion_states
    assert OrderStatus.delivered in completion_states
    assert OrderStatus.dropped_at_terminal in completion_states
