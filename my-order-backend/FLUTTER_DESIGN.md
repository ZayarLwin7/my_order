# My-Order Flutter Apps — Complete Design Document

> **Purpose**: Complete UI/UX blueprint for the My-Order mobile platform, mapped directly to the backend API.
> **Structure**: TWO apps (Grab model) — see Section 1A.
> **Note**: Section 14 covers Partner ("Merchant") features inside the Customer app.

---

## 1. Project Overview

| Item | Value |
|------|-------|
| **App Name** | My Order |
| **Backend** | FastAPI (`my-order-backend`) |
| **API Base URL (dev)** | `http://10.0.2.2:8000/api/v1` (Android emulator) / `http://localhost:8000/api/v1` (iOS sim) |
| **API Base URL (prod)** | `https://api.my-order.com/api/v1` (placeholder) |
| **Auth** | JWT Bearer tokens (`Authorization: Bearer <token>`) |
| **State Management** | Riverpod (recommended) or Provider |
| **HTTP Client** | Dio (interceptors for token + error handling) |
| **Maps** | google_maps_flutter |
| **Min Flutter Version** | 3.x, Dart 3 |

### User Roles → App Experiences

The backend `UserRole` enum drives which app/flow a user gets:

```
sender → My Order Customer app (ordering + Merchant/partner features)
rider  → My Order Rider app (delivery work)
staff  → My Order Staff app (office walk-in order creation)
admin  → Admin web dashboard (Flutter web, Phase 5)
```

---

## 1A. Three-App Architecture ⭐

My-Order ships **three installable mobile apps from one codebase**, plus a web dashboard for admin:

| | 📱 **My Order** (Customer) | 🏍️ **My Order Rider** | 🏢 **My Order Staff** | 🖥️ Admin Web |
|---|---|---|---|---|
| **Package ID** | `com.myorder.app` | `com.myorder.rider` | `com.myorder.staff` | web build |
| **App store name** | "My Order" | "My Order Rider" | "My Order Staff" | n/a (internal URL) |
| **Who installs** | Senders / Merchants | Riders | Office staff | Admins (browser) |
| **Roles served** | `sender` (+ Merchant features) | `rider` | `staff` | `admin` |
| **Screens** | P1–P17 (Section 3) | R1–R9 (Section 3) | W1–W5 (Section 3) | A1–A8 (Phase 5, Flutter web) |

### Why multiple apps, one codebase

- **Flutter flavors**: single repo, shared core (API client, models, theme, widgets); different entrypoints, branding, and screens per flavor
- Store separation: customer reviews don't mix with rider or staff apps — Grab, Gojek, Uber all do this
- Smaller per-app downloads; each app only ships its own screens
- Staff app stays lightweight: walk-in order creation only, no customer features

### Role enforcement at login (critical!)

All three apps hit the same backend `/auth/login`. After login the app checks `/users/me`:

```dart
// Customer app:
if (profile.role != UserRole.sender) {
  showError("This account is not a customer account. Please use the correct My Order app.");
  await logout();
}

// Rider app:
if (profile.role != UserRole.rider) { /* same pattern */ }

// Staff app:
if (profile.role != UserRole.staff) { /* same pattern */ }
```

Admin accounts are blocked from all three mobile apps — they use the Phase 5 web dashboard.


### Admin (Phase 5, decided)

Admin is a **Flutter web dashboard** (A1–A8), not a mobile app — desk work fits the browser, and admins don't need a store install. Staff walk-in (W1–W5) ships as the third mobile app above.

### Impact on current Phase 1 build

The existing `my_order_mobile` project becomes the shared repo. Changes needed:
1. Split current auth/home screens into `lib/customer/`, add `lib/rider/` and `lib/staff/` shells
2. Add three entrypoints + Android flavor config (productFlavors in build.gradle)
3. Add role-guard on login per Section 1A table above
4. Rider app's post-login state machine: no profile → R8 apply form; pending → R9 status; approved → dashboard (needs backend `rider_status` first)

---

## 2. Backend API Reference (What the App Calls)

All endpoints are prefixed with `/api/v1`.

### Auth
| Method | Endpoint | Used By | Purpose |
|--------|----------|---------|---------|
| POST | `/auth/register` | sender, rider | Register (name, phone, password, role) |
| POST | `/auth/login` | all | Login → `{access_token}` |

### Quotes & Pricing
| Method | Endpoint | Used By | Purpose |
|--------|----------|---------|---------|
| POST | `/quotes` | sender, staff | Get delivery quote |
| GET | `/quotes/{id}` | sender, staff | Retrieve own quote |

Quote request payload (door-to-door):
```json
{
  "delivery_mode": "door_to_door",
  "destination_city": "Yangon",
  "destination_township": "kamayut",
  "dropoff_address": "string",
  "dropoff_lat": 16.85,
  "dropoff_lng": 96.18,
  "fee_payer": "sender"
}
```

Quote response contains: `estimated_fee_mmk`, `maximum_fee_mmk`, `base_fee_mmk`, `zone_surcharge_mmk`, `partner_discount_mmk`, `expires_at`.

### Orders
| Method | Endpoint | Used By | Purpose |
|--------|----------|---------|---------|
| POST | `/orders` | sender | Create order from quote |
| POST | `/orders/walkin` | staff | Create walk-in order |
| PATCH | `/orders/{id}/assign` | admin | Assign rider |
| PATCH | `/orders/{id}/verify-item-size` | rider | Verify size at pickup |
| PATCH | `/orders/{id}/confirm-final-fee` | sender | Sender approves final fee |
| PATCH | `/orders/{id}/approve-final-fee` | admin | Admin overrides fee approval |
| PATCH | `/orders/{id}/status` | rider, admin | Status transitions |
| PATCH | `/orders/{id}/cancel` | sender/admin | Cancel order |

Order status enum:
`pending → assigned → picked_up → delivered / dropped_at_terminal / delivery_failed → returned / cancelled_post_pickup / disputed / cancelled / returned`

### Riders
| Method | Endpoint | Used By | Purpose |
|--------|----------|---------|---------|
| POST | `/riders/apply` | rider | Submit application (nrc, license, plate) |
| PATCH | `/riders/{app_id}/approve` | admin | Approve application |
| PATCH | `/riders/{app_id}/reject` | admin | Reject application |

### Rider Earnings (prefix `/riders`)
| Method | Endpoint | Used By | Purpose |
|--------|----------|---------|---------|
| GET | `/riders/me/earnings/summary` | rider | Own earnings summary |
| GET | `/riders/me/earnings` | rider | Own earnings list |
| GET | `/riders/payouts/me` | rider | Own payouts |

### Rider Wallet (prefix `/riders`, admin views)
| Method | Endpoint | Used By | Purpose |
|--------|----------|---------|---------|
| GET | `/riders/{id}/wallet` | admin | Wallet balance + alert flag |
| GET | `/riders/{id}/wallet/transactions` | admin | Transaction history |
| POST | `/riders/{id}/wallet/remittances` | admin | Record remittance |
| PATCH | `/riders/{id}/suspend` | admin | Suspend rider |

### Partners
| Method | Endpoint | Used By | Purpose |
|--------|----------|---------|---------|
| POST | `/partners/apply` | sender | Apply as partner |
| GET | `/partners/settlements/me/summary` | partner | Settlement summary |
| GET | `/partners/settlements/me` | partner | Own settlements |

### Disputes
| Method | Endpoint | Used By | Purpose |
|--------|----------|---------|---------|
| POST | `/disputes` | sender | File dispute (order_id, reason, description) |
| GET | `/disputes/{id}` | filer/admin | View dispute |
| PATCH | `/disputes/{id}/resolve` | admin | Resolve dispute |

Dispute reasons: `damaged`, `missing`, `cod_mismatch`, `other`
Resolution types: `full_refund`, `partial_refund`, `wallet_adjustment`, `claim_denied`

### Tracking
| Method | Endpoint | Used By | Purpose |
|--------|----------|---------|---------|
| GET | `/tracking/{order_id}` | participants | Tracking milestones |

---

## 3. Screen Inventory

**Total: 37 screens** across 2 apps + ops (34 core + P15–P17 merchant screens).
Screens S1–S4 and P* live in the **Customer app**; R* live in the **Rider app** (see Section 1A).

### Shared Auth Screens (4 — duplicated per app with fixed role)
| # | Screen | Customer app | Rider app |
|---|--------|--------------|-----------|
| S1 | Splash | ✓ | ✓ |
| S3 | Login (+ wrong-app role guard) | ✓ | ✓ |
| S4 | Register (role fixed: sender / rider) | ✓ sender | ✓ rider → forces R8 apply form |

*(S2 Onboarding optional per app.)*

### Customer App — Sender Flow (14 screens)
| # | Screen | Key Elements |
|---|--------|--------------|
| P1 | Home Dashboard | Active orders card, "New Order" FAB, recent orders list |
| P2 | Delivery Mode Select | Two big cards: Door-to-Door 🚪 / Bus Terminal 🚌 |
| P3 | Pickup Location | Address field + map picker + confirm |
| P4 | Dropoff — D2D | City dropdown (Yangon/Mandalay), township dropdown, address, map pin |
| P5 | Dropoff — Bus Terminal | Town field, terminal name, bus line |
| P6 | Recipient Details | Recipient name + phone |
| P7 | Item & Payment | Item value (MMK), COD amount (partners only, else hidden/disabled), fee payer toggle (me/recipient), terms checkbox |
| P8 | Quote Review | Price breakdown card (base + surcharge − discount), estimated fee, max fee, expiry countdown, Confirm button |
| P9 | Order Created Success | Success animation, order ID, "Track Order" CTA |
| P10 | Fee Confirmation | Original vs new fee comparison, Accept / Dispute buttons |
| P11 | Order Detail | Status timeline, rider card (name/phone/call), addresses, fee summary, actions (cancel/dispute) |
| P12 | Order History | Tab bar: Active / Completed / Cancelled, order cards |
| P13 | File Dispute | Reason chips (damaged/missing/COD mismatch/other), description, photo attach (future), submit |
| P15 | Partner Application Form | Business name/address/contact phone → `POST /partners/apply` |
| P16 | Application Status | pending_review / rejected + reviewer notes, reapply button |
| P17 | Partner Dashboard Tab | Settlement summary, settlement history, payout method *(approved partners only)* |

**Sender screen total: 17** (P14 reserved — see Section 14 for partner renumbering note)

### Rider App — Rider Flow (9 screens)
Post-login state machine gates entry to the dashboard:
```
login → GET /users/me
  ├─ rider_status = none        → R8 apply form (mandatory)
  ├─ rider_status = pending_review → R9 "under review"
  ├─ rider_status = rejected    → R9 + reviewer notes + Reapply
  └─ rider_status = approved    → R1 dashboard
```
(Requires backend `/users/me` extension with `rider_status` — same pattern as partner_status.)

| # | Screen | Key Elements |
|---|--------|--------------|
| R1 | Rider Dashboard | Today's earnings header, assigned orders list, availability toggle |
| R2 | Assigned Order Detail | Pickup address + navigate button, dropoff info, item value/COD, action buttons |
| R3 | Verify Item Size | Size selector (uses backend item_size_rates), recalculated fee display, Confirm button |
| R4 | Out for Delivery | Map route, dropoff details, COD collect amount, buttons: Delivered ✅ / Failed ❌ / Dropped at Terminal 🏢 |
| R5 | COD Collection | Amount due, collected confirmation keypad, note field |
| R6 | Wallet | Balance card, alert banner (if ≥ threshold), transaction list |
| R7 | Earnings | Summary cards (today/week/month), per-order list, payouts tab |
| R8 | Rider Application | NRC, license no., vehicle plate, photo upload → POST /riders/apply → R9 |
| R9 | Application Status | pending_review / approved / rejected + notes, reapply option |

### Staff Flow (5 screens)
| # | Screen | Key Elements |
|---|--------|--------------|
| W1 | Staff Dashboard | "New Walk-in Order" primary button, today's walk-in count, recent orders |
| W2 | Walk-in Customer Info | Walk-in customer name + phone (manual entry), recipient details |
| W3 | Walk-in Quote & Pay | Quote breakdown, payment received checkbox (no COD allowed), Create Order button |
| W4 | Walk-in Order List | Orders created by this staff member, filter by status |
| W5 | Walk-in Success | Receipt view with order ID for customer copy |

### Admin Panel (8 screens — can be Flutter tablet/web)
| # | Screen | Key Elements |
|---|--------|--------------|
| A1 | Admin Dashboard | Stats cards: pending assignments, open disputes, pending applications, wallet alerts |
| A2 | Order Queue | Pending orders list → assign dialog (rider picker) |
| A3 | Rider Applications | List → detail → Approve/Reject with notes |
| A4 | Partner Applications | Same pattern |
| A5 | Disputes Center | Open disputes → resolve sheet: resolution type, amount, payer |
| A6 | Finance | Platform ledger table, reconciliation view |
| A7 | Rider Wallets | Per-rider balance, alert flags, remittance recording |
| A8 | Pricing Config | Delivery zones CRUD, item size rates CRUD, partner discounts |

---

## 4. Navigation Architecture

```
main.dart
└── MaterialApp
    └── AuthGate (Riverpod StreamProvider on stored token)
        ├── No token → Onboarding → Login/Register
        └── Token → decode role
            ├── sender → SenderShell (BottomNav: Home, History, Profile)
            ├── rider  → RiderShell  (BottomNav: Dashboard, Wallet, Earnings, Profile)
            ├── staff  → StaffShell  (BottomNav: Dashboard, Orders, Profile)
            └── admin  → AdminShell  (Rail/Drawer: Dashboard, Orders, Users, Finance, Config)
```

- **go_router** for declarative routes with guards.
- Route guards check: token validity → role match.
- Deep link support: `/order/{id}`, `/dispute/{id}` (for push notifications later).

---

## 5. Design System

### Colors
```dart
class MOColors {
  // Brand
  static const primary      = Color(0xFF1A73E8); // Trust blue
  static const primaryDark  = Color(0xFF0D47A1);
  static const accent       = Color(0xFFFFB300);  // Amber accent

  // Role identities
  static const senderColor  = Color(0xFF2E7D32); // Green
  static const riderColor   = Color(0xFFEF6C00); // Orange
  static const staffColor   = Color(0xFF6A1B9A); // Purple
  static const adminColor   = Color(0xFF37474F); // Slate

  // Status colors (map to backend OrderStatus)
  static const pending      = Color(0xFFF9A825); // amber
  static const assigned     = Color(0xFF1E88E5); // blue
  static const inTransit    = Color(0xFF00897B); // teal (picked_up)
  static const delivered    = Color(0xFF43A047); // green
  static const terminal     = Color(0xFF00ACC1); // cyan (dropped_at_terminal)
  static const failed       = Color(xFFE53935);  // red (delivery_failed)
  static const disputed     = Color(0xFF8E24AA); // purple
  static const cancelled    = Color(0xFF757575); // grey
}
```

### Typography
```dart
// Supports Myanmar Unicode - use Google Fonts
fontFamily: 'Noto Sans Myanmar' // fallback for Myanmar text
displayFont: 'Inter'            // headings/numbers
```

- Currency always displayed as: `5,000 MMK` (thousand separators)

### Spacing & Shape
- Base unit: **8px grid**
- Card radius: **16px**, buttons: **12px**
- Elevation: cards 2, dialogs 8

### Dark Mode
- Support light/dark via Material 3 `ColorScheme.fromSeed()`

---

## 6. Reusable Widgets Library

| Widget | Usage | Props |
|--------|-------|-------|
| `MOButton` | All buttons | label, variant(primary/outline/danger), loading, disabled |
| `MOTextField` | All inputs | MMK amount mode, phone validator (+95 format) |
| `MOOrderCard` | Order lists | order, onTap, showRider |
| `MOStatusBadge` | Status display | OrderStatus → color+label+icon |
| `MOTimeline` | Tracking milestones | milestones[] from tracking endpoint |
| `MOPriceBreakdown` | Quote screens | baseFee, surcharge, discount, total |
| `MOMapPicker` | D2D address entry | initialPosition, onSelected(lat,lng) |
| `MORiderCard` | Order detail | rider name, phone, call/chat buttons |
| `MOEmptyState` | Empty lists | icon, message, actionLabel |
| `MOErrorView` | API failures | retry callback |
| `MOConfirmDialog` | destructive actions | title, message, danger flag |
| `MOSnackBar` | feedback | success/error/info variants |

---

## 7. State & Data Layer

```
lib/
├── main.dart
├── core/
│   ├── api/
│   │   ├── dio_client.dart          # Base client + interceptors
│   │   ├── auth_interceptor.dart    # Attach JWT, handle 401 → logout
│   │   └── api_endpoints.dart       # All endpoint constants
│   ├── storage/
│   │   └── secure_storage.dart      # JWT storage (flutter_secure_storage)
│   ├── theme/
│   │   ├── colors.dart
│   │   ├── text_styles.dart
│   │   └── theme.dart
│   ├── widgets/                     # Reusable widget library (Section 6)
│   └── utils/
│       ├── formatters.dart          # MMK currency, phone, dates
│       └── validators.dart          # Myanmar phone regex, password rules
├── features/
│   ├── auth/
│   │   ├── models/user.dart         # Mirrors UserOut schema
│   │   ├── providers/auth_provider.dart
│   │   └── screens/ (login, register)
│   ├── sender/
│   │   ├── providers/order_provider.dart
│   │   ├── screens/ (P1–P14)
│   │   └── widgets/
│   ├── rider/
│   │   ├── providers/rider_provider.dart
│   │   ├── screens/ (R1–R9)
│   │   └── widgets/
│   ├── staff/
│   │   ├── screens/ (W1–W5)
│   │   └── providers/staff_provider.dart
│   └── admin/
│       ├── screens/ (A1–A8)
│       └── providers/admin_provider.dart
└── routing/
    ├── app_router.dart              # go_router config + guards
    └── shell_router.dart            # Bottom nav shells per role
```

### API Models (mirror backend Pydantic schemas)
```dart
UserOut, Token, DeliveryQuoteOut, OrderOut, TrackingOut,
WalletOut, WalletTransactionOut, DisputeOut, PartnerSettlementSummary,
RiderEarningsSummary, RiderApplicationOut, PartnerApplicationOut
```

### Error Handling Convention
Backend errors return `{"detail": "message"}`:
- 400/403/404 → show `detail` in snackbar
- 401 → clear token → force re-login
- 422 → show field-level validation
- 429 → "Too many attempts" message with retry-after

---

## 8. Critical UX Flows

### Flow A: Sender Creates Door-to-Door Order
```
P1 → P2(mode) → P3(pickup) → P4(dropoff) → P6(recipient)
→ P7(item/payment) → P8(quote review)
   [POST /quotes] → shows estimate; user has 30min before expiry
→ Confirm [POST /orders] → P9 success
→ Poll GET /tracking/{id} every 15s until assigned
→ Notification: "Rider assigned!" 
```

### Flow B: Fee Adjustment (the tricky one!)
```
Backend auto-confirms if final ≤ authorized_max.
If surcharge exceeds authorization → price_confirmed_at stays null:

Sender sees banner on P11: "⚠️ Fee needs your confirmation"
→ P10 shows: Estimate 4,000 / Final 5,000 MMK
→ [Accept] → PATCH /confirm-final-fee → status continues
→ [Dispute] → contact support path
(Rider cannot pick up until confirmed! Show this clearly.)
```

### Flow C: Rider Delivery with COD
```
R2(order detail) → [Start] → R3 verify item size
[PATCH /verify-item-size]
→ If fee needs sender confirmation → show "Waiting for sender…" state
→ Else → R4 out-for-delivery
→ At dropoff: COD? → R5 collection screen (amount = cod_amount [+fee if recipient pays])
→ Mark delivered [PATCH /status {status: delivered}]
→ Backend credits rider wallet + creates partner ledger entries automatically
→ Success animation → back to R1, earnings updated
```

### Flow D: Walk-in Customer (Staff)
```
Customer arrives without app → W1 → W2 enter customer name/phone
→ same quote flow (POST /quotes works for staff now)
→ W3: collect cash payment at office (COD disabled by backend)
→ [Create Order] POST /orders/walkin
→ W5 receipt printed/shown → hand to customer
```

### Flow E: Dispute
```
P11(delivered order) → [File Dispute] → P13
→ select reason → submit [POST /disputes]
→ Order becomes "disputed", partner credit frozen
→ Admin resolves in A5 → sender notified of outcome
(48h window enforced by backend — show countdown if near expiry)
```

---

## 9. Polling & Real-Time Strategy

Backend currently has REST-only endpoints (no WebSocket).

| Data | Strategy |
|------|----------|
| Order status (active orders) | Poll `/tracking/{id}` every 15s while screen open |
| Rider dashboard | Poll assigned orders every 30s |
| New-order notification | Phase 3: Firebase Cloud Messaging |
| Live rider location | Phase 3: WebSocket or FCM data messages |

---

## 10. Security Checklist

- ✅ JWT in `flutter_secure_storage` (never SharedPreferences)
- ✅ Logout clears storage + provider state
- ✅ 401 interceptor → automatic re-login redirect
- ✅ Certificate pinning (prod)
- ✅ No sensitive data in logs
- ✅ Phone numbers masked in support views: `09***123`

---

## 11. Build Phases (Two-App Structure) ⭐

### Phase 1 — Flavor Split + Customer Auth ✅ (in progress)
1. ~~Project setup, theme, routing, Dio client, secure storage~~ done (single app)
2. Split into flavors: `main_customer.dart` / `main_rider.dart`, Android productFlavors, shared `core/`
3. Customer app auth: S1/S3/S4 (role fixed to sender; wrong-role guard)
4. Rider app shell: S1/S3/S4-R (role fixed to rider; wrong-role guard)

### Phase 2 — Customer Order Core
5. Backend: extend `/users/me` with `rider_status` (+ tests)
6. P1 home + P2–P9 create-order wizard + quote integration
7. P11 order detail + P12 history with polling

### Phase 3 — Rider App Complete
8. Rider gating state machine: `/users/me.rider_status` → R8 apply form → R9 status → R1
9. R2 order detail + R3 verify-size + R4 delivery + R5 COD
10. R6 wallet + R7 earnings

### Phase 4 — Merchant + Fee Confirmation + Disputes
11. P15–P17 merchant application & settlements tab (Section 14)
12. P10 fee confirmation flow
13. P13 dispute filing

### Phase 5 — Staff App + Admin Web
14. Staff app: W1–W5 walk-in module (needs backend staff-account provisioning endpoint or DB seeding)
15. Admin web dashboard (Flutter web): A1–A8
16. Admin/staff accounts blocked from Customer & Rider apps by role guard

### Phase 6 — Polish
17. Push notifications (FCM), dark mode, Myanmar localization, offline handling

---

## 12. Dependencies (pubspec.yaml preview)

```yaml
dependencies:
  flutter_riverpod: ^2.5.1
  go_router: ^14.2.0
  dio: ^5.4.0
  flutter_secure_storage: ^9.2.2
  google_maps_flutter: ^2.6.0
  geolocator: ^12.0.0
  intl: ^0.19.0                # MMK formatting
  google_fonts: ^6.2.0
  flutter_local_notifications: ^17.0.0

dev_dependencies:
  build_runner: ^2.4.9
  json_serializable: ^6.8.0    # model codegen matching backend schemas
```

---

## 14. Partner Sender Features (Regular Sender vs Approved Partner)

### How Partner Status Works (Backend Reality)

- Both regular senders and partners share `UserRole.sender`
- Partner status lives in the separate `PartnerProfile` table:
  - `active_status: true` + not suspended → **approved partner**
  - No profile / pending / rejected → **regular sender**
- A sender becomes a partner: apply → admin approves → COD unlocked
- Key backend rule: **COD orders (`cod_amount > 0`) are rejected with 403 unless the sender is an active partner** — walk-in orders can never have COD

### Partner Status Check in App

```dart
// The app needs to know partner status after login.
// Option A (preferred): extend a "me" endpoint to include partner info
class SenderProfile {
  final String id;
  final String name;
  final String phone;
  final PartnerStatus status;   // none | pendingReview | approved | rejected
  final PartnerProfile? partner; // business info, discount, settlement method
}

enum PartnerStatus { none, pendingReview, approved, rejected }
```

> ⚠️ **Backend gap to fill**: There is currently no `GET /users/me` endpoint returning
> joined partner status. Before Phase 1 we should add one (small change) so the app
> doesn't have to infer status from failed COD attempts. Fallback without it:
> attempt COD → on 403 show "Apply for Partner" dialog.

---

### Additional Screens (P15–P17)

| # | Screen | Shown To | Key Elements |
|---|--------|----------|--------------|
| P15 | Partner Application Form | sender without profile | Business name, address, contact phone → `POST /partners/apply` |
| P16 | Application Status | sender with pending/rejected application | Status badge (pending_review / rejected + reviewer notes), reapply button when rejected |
| P17 | Partner Dashboard Tab | approved partner | Settlement summary cards, settlement history, payout method display |

*(P14 from the original inventory is now P15 — renumbered to keep sender flow together.)*

### Updated Sender Screen Count

| Flow | Screens |
|------|---------|
| Regular sender | P1–P13 (+ P15/P16 if they choose to apply) |
| Approved partner | P1–P13 + P17, COD enabled everywhere |

---

### Conditional UI Rules

```dart
// P7 Item & Payment screen
if (profile.status == PartnerStatus.approved && !partner.suspended) {
  // COD field ENABLED, shows partner discount note
} else {
  // COD field DISABLED with helper text:
  // "Apply for Partner status to accept Cash on Delivery orders"
  // + tap → navigates to P15
}

// P1 Home Dashboard
switch (profile.status) {
  case none:
    showCard("Unlock COD — become a Partner", onTap: () => go(P15));
  case pendingReview:
    showBanner("Partner application under review", style: info);
  case rejected:
    showBanner("Application rejected: ${notes}", action: "Reapply" → P15);
  case approved:
    showPartnerTab(P17);  // settlements visible in bottom nav or drawer
}

// P8 Quote Review — partners see discount line item
if (isApprovedPartner) {
  PriceBreakdown(baseFee, surcharge, -discount, total);  // partner_discount_mmk from quote
}

// P12 Order History — partners get an extra tab
tabs = isApprovedPartner
    ? [Active, Completed, Cancelled, Settlements]
    : [Active, Completed, Cancelled];
```

### Partner Journey Map

```
Regular sender (P1)
  → sees "Become a Partner" promo card
  → P15 apply form [POST /partners/apply]
  → P16 "Under review"
      ├─ Admin approves (A4) → push notification
      │    → app refreshes profile → status=approved
      │    → P1 now shows Settlements tab (P17), COD field live on P7
      └─ Admin rejects → P16 shows reviewer_notes + Reapply button
```

### Partner Data Endpoints Used by P17

| Endpoint | Purpose |
|----------|---------|
| `GET /partners/settlements/me/summary` | Totals: available, on_hold, paid |
| `GET /partners/settlements/me` | Settlement history list |
| `GET /partners/{id}/ledger` *(admin)* | Full ledger entries |
| `PATCH /partners/me/payout-method` | Save MMQR account name/reference |

### Edge Cases to Handle

1. **Suspended partner mid-COD**: order creation returns 403 → show suspension notice
2. **Discount changes**: quote stores snapshot at request time — old quotes keep old discounts
3. **Settlement visibility**: only show settlements where `status != draft`; amounts use ledger aggregation, never a balance column
4. **COD dispute freeze**: when order is disputed, P17 summary should reflect `on_hold` amounts (backend moves credit status automatically)

---

## 15. Status & Decisions Log

| Decision | Choice | Status |
|----------|--------|--------|
| Flutter env | SDK 3.47.1 + Android emulator | ✅ ready |
| State management | **Riverpod** | ✅ decided |
| Maps | flutter_map/OpenStreetMap first, no key needed | ✅ decided |
| `GET /users/me` | Added with partner_status (+5 tests passing) | ✅ done |
| App structure | **Three apps, one codebase**: Customer + Rider + Staff flavors; Merchant inside Customer app; Admin = Flutter web (Phase 5) | ✅ decided |
| Target device | Android emulator (Pixel 9) primary | ✅ decided |
| Phase 1 auth flow | Working end-to-end on emulator (register→login→role home) | ✅ verified |

### Remaining backend item before Phase 3
- Extend `/users/me` with `rider_status` (same pattern as partner_status) — small change, tested pattern already exists.

Then just say **"continue Phase 1"** (flavor split) and I'll restructure the codebase.
