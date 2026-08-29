from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.order import DeliveryMode, FeePayer
from app.schemas.pricing import DeliveryQuoteCreate


def test_door_to_door_quote_requires_city_township_and_address_coordinates():
    with pytest.raises(ValidationError, match="city, township, and drop-off"):
        DeliveryQuoteCreate(
            delivery_mode=DeliveryMode.door_to_door,
            destination_city="Yangon",
            destination_township="Hlaing",
        )


def test_door_to_door_quote_accepts_yangon_destination_inputs():
    quote = DeliveryQuoteCreate(
        delivery_mode=DeliveryMode.door_to_door,
        destination_city="Yangon",
        destination_township="Hlaing",
        dropoff_address="Insein Road",
        dropoff_lat=16.85,
        dropoff_lng=96.13,
        fee_payer=FeePayer.recipient,
    )

    assert quote.destination_township == "Hlaing"
    assert quote.fee_payer == FeePayer.recipient


def test_terminal_quote_requires_town_terminal_and_bus_line():
    with pytest.raises(ValidationError, match="destination_town, terminal_name, and bus_line"):
        DeliveryQuoteCreate(
            delivery_mode=DeliveryMode.bus_terminal,
            destination_town="Taunggyi",
        )


def test_terminal_quote_accepts_other_town_without_township():
    quote = DeliveryQuoteCreate(
        delivery_mode=DeliveryMode.bus_terminal,
        destination_town="Taunggyi",
        terminal_name="Aung Mingalar Terminal",
        bus_line="Yangon-Taunggyi",
    )

    assert quote.destination_city is None
    assert quote.destination_town == "Taunggyi"


def test_fee_components_can_be_reconciled_without_rounding_loss():
    base = Decimal("3500")
    zone_surcharge = Decimal("1000")
    partner_discount = Decimal("500")
    item_size_surcharge = Decimal("1500")

    estimate = base + zone_surcharge - partner_discount
    final_fee = estimate + item_size_surcharge

    assert estimate == Decimal("4000")
    assert final_fee == Decimal("5500")
