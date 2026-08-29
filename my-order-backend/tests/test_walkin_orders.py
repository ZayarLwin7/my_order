"""Tests for walk-in order functionality (staff creating orders for customers without accounts)"""
import pytest


def test_staff_role_exists():
    """Verify staff role was added to the system"""
    from app.models.user import UserRole
    assert hasattr(UserRole, 'staff')
    assert UserRole.staff.value == 'staff'


def test_order_model_has_walkin_fields():
    """Verify Order model has walk-in fields"""
    from app.models.order import Order
    assert hasattr(Order, 'is_walkin')
    assert hasattr(Order, 'walkin_sender_name')
    assert hasattr(Order, 'walkin_sender_phone')
    assert hasattr(Order, 'created_by_staff_id')


def test_walkin_order_schema_exists():
    """Verify WalkinOrderCreate schema exists"""
    from app.schemas.order import WalkinOrderCreate
    assert WalkinOrderCreate is not None


# TODO: Add integration tests with proper database fixtures
# These would test:
# - Staff can create walk-in orders
# - Walk-in orders cannot have COD
# - Senders cannot use /walkin endpoint
# - Existing sender order flow still works
