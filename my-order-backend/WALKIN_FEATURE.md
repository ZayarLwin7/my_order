# Walk-in Order Feature - Implementation Summary

## Overview
Added support for office staff to create orders on behalf of walk-in customers who don't have accounts.

## Changes Made

### 1. Database Schema (Migration: 971b73516acb)
- Added `staff` to `UserRole` enum
- Added 4 new columns to `orders` table:
  - `created_by_staff_id` (UUID, FK to users) - Which staff member created it
  - `is_walkin` (Boolean) - Flag for walk-in orders
  - `walkin_sender_name` (String) - Walk-in customer's name
  - `walkin_sender_phone` (String) - Walk-in customer's phone

### 2. Models Updated
- **app/models/user.py**: Added `UserRole.staff`
- **app/models/order.py**: Added walk-in fields and `created_by_staff` relationship

### 3. Schemas Updated
- **app/schemas/order.py**: 
  - Added `WalkinOrderCreate` schema for staff order creation
  - Updated `OrderOut` to include walk-in fields

### 4. API Endpoints
- **New**: `POST /api/v1/orders/walkin` - Staff creates orders for walk-in customers
  - Only accessible by users with `UserRole.staff`
  - Requires walk-in customer name and phone
  - **COD is disabled** for walk-in orders (cash at office only)
  - All other validation same as regular orders

### 5. Business Rules
- **Staff role** can only create walk-in orders (not regular sender orders)
- **Walk-in orders cannot have COD** - walk-in customers must pay at office
- **Audit trail** - `created_by_staff_id` tracks which staff member created the order
- **Walk-in customer details** stored separately (not creating fake accounts)
- **Existing flows untouched** - sender, rider, admin flows work exactly as before

### 6. Tests
- Created `tests/test_walkin_orders.py` with test scaffolding

### 7. Documentation
- Updated README.md with:
  - Walk-in customer support in features
  - Staff role in authentication section
  - New `/walkin` endpoint in API documentation

## How It Works

### Staff Workflow
1. Walk-in customer comes to office
2. Staff member (logged in with staff account) gets a delivery quote
3. Staff creates order via `POST /api/v1/orders/walkin` with:
   - Customer's name and phone (in `walkin_sender_name/phone` fields)
   - Recipient details
   - Payment collected at office (no COD)
4. Order enters normal flow (pending → assigned → delivered)

### Key Differences from Regular Orders
| Feature | Regular Order | Walk-in Order |
|---------|---------------|---------------|
| Creator | Sender (self) | Staff (on behalf) |
| Account needed | Yes | No |
| COD allowed | Yes (for partners) | No |
| sender_id | Customer's user ID | Staff's user ID |
| Audit trail | N/A | `created_by_staff_id` |

## Example API Call

```bash
POST /api/v1/orders/walkin
Authorization: Bearer <staff_token>
Content-Type: application/json

{
  "quote_id": "550e8400-e29b-41d4-a716-446655440000",
  "walkin_sender_name": "Ma Aye Aye",
  "walkin_sender_phone": "09888888888",
  "recipient_name": "Ko Ko",
  "recipient_phone": "09777777777",
  "pickup_address": "123 Office St, Yangon",
  "pickup_lat": 16.8409,
  "pickup_lng": 96.1735,
  "item_value": 10000,
  "cod_amount": 0,
  "authorized_max_fee_mmk": 7000,
  "terms_accepted": true
}
```

## Database Migration Status
✅ Migration applied successfully: `971b73516acb_add_staff_role_and_walkin_order_fields`

## Backward Compatibility
✅ **All existing functionality preserved**:
- Sender orders work exactly as before
- Rider flows unchanged
- Admin operations unchanged
- Partner COD logic unchanged
- Financial tracking unchanged

## Next Steps (Optional)
- Create first staff account manually in database
- Train office staff on the new endpoint
- Consider adding staff management endpoints (list staff, create staff accounts)
- Add reporting: orders created by each staff member
- Consider allowing walk-in customers to "claim" their orders later if they register

---

**Migration file**: `alembic/versions/971b73516acb_add_staff_role_and_walkin_order_fields.py`
**Test file**: `tests/test_walkin_orders.py`
**Date**: 2026-08-23
