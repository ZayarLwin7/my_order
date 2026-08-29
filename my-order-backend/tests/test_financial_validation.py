from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.dispute import RefundPayer, ResolutionType
from app.schemas.dispute import DisputeResolveRequest
from app.schemas.rider_earnings import RiderCompensationRateCreate, RiderPayoutCreate
from app.schemas.wallet import RemittanceAllocationRequest, RemittanceRequest


def test_remittance_requires_positive_amount_and_reference():
    with pytest.raises(ValidationError):
        RemittanceRequest(amount=Decimal("0"), reference="BANK-001")

    with pytest.raises(ValidationError):
        RemittanceRequest(amount=Decimal("1000"), reference="")

    request = RemittanceRequest(amount=Decimal("1000"), reference="BANK-001")
    assert request.amount == Decimal("1000")


def test_remittance_allocation_requires_at_least_one_order():
    with pytest.raises(ValidationError):
        RemittanceAllocationRequest(allocations=[])


def test_compensation_rate_must_be_positive():
    with pytest.raises(ValidationError):
        RiderCompensationRateCreate(per_completed_way_mmk=Decimal("0"), effective_from="2026-08-21")


def test_rider_payout_salary_cannot_be_negative():
    with pytest.raises(ValidationError):
        RiderPayoutCreate(
            rider_user_id="00000000-0000-0000-0000-000000000000",
            period_start="2026-08-01",
            period_end="2026-08-31",
            salary_amount=Decimal("-1"),
        )


def test_refund_resolution_requires_positive_amount_when_supplied():
    with pytest.raises(ValidationError):
        DisputeResolveRequest(
            resolution_type=ResolutionType.full_refund,
            resolved_amount=Decimal("0"),
            refund_payer=RefundPayer.platform,
        )

    resolution = DisputeResolveRequest(
        resolution_type=ResolutionType.partial_refund,
        resolved_amount=Decimal("2500"),
        refund_payer=RefundPayer.partner,
    )
    assert resolution.resolved_amount == Decimal("2500")
