# My-Order — Run Instructions (Current Stage)

> Scope: how to run the **backend** and **frontend** as they exist *today*
> (commit `fa8a3f1`, "Fix 18 failing integration tests → green").
> This is NOT a production guide. It covers local development only.
> The project is two sibling folders under this repo root:
> - `my-order-backend/`  — FastAPI + SQLAlchemy 2.0 + PostgreSQL (Alembic)
> - `my_order_mobile/`    — Flutter app (4 flavors: customer / rider / staff / admin)
>
> Test status: **169 passed, 0 failed** (backend integration suite).

---

## 0. Prerequisites (verified on this machine)

| Tool | Required | Notes |
|------|----------|-------|
| Python | 3.11+ (using 3.13.4 via `my-order-backend/venv`) | |
| PostgreSQL | 14+ | A local server is required for the backend and its tests |
| Flutter SDK | 3.13.1+ | `flutter --version` works; no emulator needed to run logic checks |
| A local Postgres superuser | `postgres` | Used for DB creation below |

Backend dependencies are already installed in `my-order-backend/venv`.
Frontend dependencies are not fetched yet — you run `flutter pub get` once.

---

## 1. Backend

### 1.1 Start PostgreSQL (if not already running)

Using Homebrew PostgreSQL 14 on this machine:

```bash
export PATH="/opt/homebrew/opt/postgresql@14/bin:$PATH"
# Create the data dir once (first time only):
# initdb -D /tmp/mo_pgdata -U postgres --auth=trust
pg_ctl -D /tmp/mo_pgdata -l /tmp/mo_pg.log -o "-p 5432" start
sleep 2
createdb -p 5432 -U postgres my_order          # app database
createdb -p 5432 -U postgres my_order_test     # test database
```

> If Postgres is already running on port 5432, skip `pg_ctl`. Just make sure
> the `my_order` and `my_order_test` databases exist.

### 1.2 Configure environment

A `.env` already exists in `my-order-backend/` (excluded from git). Its keys:

```env
DATABASE_URL=postgresql://postgres@localhost:5432/my_order
JWT_SECRET=<64-char random>          # generate: openssl rand -hex 32
JWT_ALGORITHM=HS256
ENVIRONMENT=development              # "production" disables /docs and enforces ALLOWED_HOSTS
ALLOWED_HOSTS=localhost,127.0.0.1
ALLOWED_ORIGINS=                    # leave empty for pure API/mobile; set if a browser calls it
DELIVERY_BASE_FEE_MMK=3500
QUOTE_EXPIRE_MINUTES=30
```

`ALLOWED_HOSTS` is only enforced when `ENVIRONMENT=production`.

### 1.3 Create tables with Alembic

Alembic reads `DATABASE_URL` from `app.config.settings` (not `alembic.ini`),
so the DB is taken from your `.env`.

```bash
cd my-order-backend
source venv/bin/activate
alembic upgrade head
```

This applies all 14 migrations and creates every table
(users, riders, orders, partners, wallets, disputes, pricing, earnings, ledgers).

### 1.4 Seed demo users (admin / customer / rider / staff)

A script inserts one account per role with known credentials so you can log into
every Flutter flavor immediately. The rider is seeded as **approved + active** so
the rider app shows the dashboard (not the apply screen).

```bash
cd my-order-backend
source venv/bin/activate
python scripts/seed_users.py
```

Seeded accounts (password for all: `Password123456`):

| Role     | Phone        | Role value |
|----------|--------------|------------|
| Admin    | 09711111111  | admin      |
| Customer | 09722222222  | sender     |
| Rider    | 09733333333  | rider      |
| Staff    | 09744444444  | staff      |

The script is idempotent — re-running refreshes the password without duplicating rows.
Requires `DATABASE_URL` (reads from `.env`).

### 1.5 Run the API server

```bash
cd my-order-backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API base URL: `http://localhost:8000/api/v1`
- Swagger UI: `http://localhost:8000/docs`  (dev only)
- ReDoc: `http://localhost:8000/redoc`      (dev only)
- Health: `GET http://localhost:8000/` → `{"status":"ok","service":"my-order-backend"}`

There is **no seeded admin** — create the first admin directly in Postgres:

```sql
INSERT INTO users (id, name, phone, password_hash, role, is_active, created_at)
VALUES (gen_random_uuid(), 'Admin', '09000000000',
        '<bcrypt hash of a password>', 'admin', true, now());
```

(Or register a sender in the app, then flip `role` to `admin` in the DB for local testing.)

### 1.5 Verified API routes (current stage)

All routers are mounted under `/api/v1`. The paths below are the *real* ones —
the old README is stale on several (e.g. it shows `/pricing/quotes`; the actual
path is `/quotes`).

Auth
- `POST /api/v1/auth/register`  (body: `name, phone, password, role`)
- `POST /api/v1/auth/login`     (body: `phone, password` → returns `access_token`)

Riders
- `POST /api/v1/riders/apply`                 (rider)
- `GET  /api/v1/riders`                       (admin — list all)
- `GET  /api/v1/riders/active`                (admin — assignable)
- `PATCH /api/v1/riders/{application_id}/approve`   (admin)
- `PATCH /api/v1/riders/{application_id}/reject`    (admin)
- `GET  /api/v1/riders/me/wallet`             (rider self)
- `GET  /api/v1/riders/me/wallet/transactions`(rider self)

Orders
- `POST /api/v1/orders`                        (sender)
- `POST /api/v1/orders/walkin`                (staff)
- `PATCH /api/v1/orders/{id}/assign`          (admin)
- `PATCH /api/v1/orders/{id}/verify-item-size`(rider)
- `PATCH /api/v1/orders/{id}/confirm-final-fee`(sender)
- `PATCH /api/v1/orders/{id}/status`          (rider/admin)
- `GET  /api/v1/tracking/{order_id}`

Pricing
- `POST /api/v1/quotes`                       (create quote)
- `GET  /api/v1/quotes/{quote_id}`
- `GET  /api/v1/admin/delivery-zones`  /  `POST /api/v1/admin/delivery-zones`
- `GET  /api/v1/admin/item-size-rates` / `POST /api/v1/admin/item-size-rates`

Rider earnings
- `POST /api/v1/riders/compensation-rates`    (admin — required before an order can reach `delivered`)
- `GET  /api/v1/riders/me/earnings`
- `POST /api/v1/riders/payouts`               (admin)

Wallets / Finance
- `GET  /api/v1/riders/{rider_user_id}/wallet`          (admin)
- `POST /api/v1/riders/{rider_user_id}/wallet/remittances` (admin)
- `GET  /api/v1/finance/platform-ledger`     (admin)
- `GET  /api/v1/finance/partner-ledger`      (admin)

Partners
- `POST /api/v1/partners/apply`              (sender; body: `business_name, business_address, contact_phone`)
- `GET  /api/v1/partners/applications`       (admin)
- `PATCH /api/v1/partners/{application_id}/approve`  (admin; body `{}`)
- `PATCH /api/v1/partners/{application_id}/reject`   (admin; body `{}`)
- `POST /api/v1/partners/ledger/release`     (admin)
- `GET  /api/v1/partners/settlements/me`     (partner self)

Disputes
- `POST /api/v1/disputes`                    (sender; `reason` must be an enum value, e.g. `damaged`)
- `GET  /api/v1/disputes`                    (admin — list)
- `PATCH /api/v1/disputes/{id}/resolve`      (admin)

### 1.6 Run the backend test suite

```bash
cd my-order-backend
source venv/bin/activate
TEST_DATABASE_URL="postgresql://postgres@localhost:5432/my_order_test" \
DATABASE_URL="postgresql://postgres@localhost:5432/my_order_test" \
JWT_SECRET="$(openssl rand -hex 32)" \
python -m pytest -q
```

Expected: **169 passed**.

> The suite creates/drops its own schema on a fresh `my_order_test` DB per run,
> so it does not touch your `my_order` dev database.

---

## 2. Frontend (Flutter)

> Current stage: the app builds the **architecture** (4 flavors, auth gate,
> login/register, admin dashboard, rider-application screens) but the **core
> delivery loop is placeholder**. Specifically:
> - Customer "New Order" → "Coming in Phase 2"
> - Staff home → "walk-in order module arrives in Phase 5"
> - Rider dashboard → "delivery flow arrives in Phase 3"
> So the UI runs, but you cannot yet create/deliver an order through it.
> The app points at `http://10.0.2.2:8000/api/v1` (Android emulator) by default.

### 2.1 Install dependencies

```bash
cd my_order_mobile
flutter pub get
```

### 2.2 Run a flavor

There is **no plain `main.dart`** — you must pick a flavor entrypoint:

```bash
# Customer app
flutter run -t lib/main_customer.dart

# Rider app
flutter run -t lib/main_rider.dart

# Staff app
flutter run -t lib/main_staff.dart

# Admin app
flutter run -t lib/main_admin.dart
```

On a physical device, point the API at your machine's LAN IP:

```bash
flutter run -t lib/main_customer.dart \
  --dart-define=API_BASE_URL=http://192.168.x.x:8000/api/v1
```

### 2.3 What you can exercise today

- Log in / register as each role (the API contract is wired up).
- Admin: view rider applications, pending orders, active riders; approve/reject/assign.
- Rider: submit an application; see pending/approved/rejected states.
- Customer/Staff: see the auth-gated home screens (order creation is stubbed).

---

## 3. End-to-end smoke test (what works now)

1. Start Postgres, `alembic upgrade head`, run `uvicorn` (§1).
2. `POST /api/v1/auth/register` a sender, a rider, an admin.
3. Rider `POST /api/v1/riders/apply`; admin `PATCH .../approve`.
4. Admin `POST /api/v1/riders/compensation-rates` (so deliveries can complete).
5. Sender `POST /api/v1/quotes` → `POST /api/v1/orders` → admin `assign` →
   rider `verify-item-size` → sender `confirm-final-fee` → rider `status` picked_up → `delivered`.
   (This full path is exactly what the integration tests cover and is green.)

---

## 4. Known gaps at this stage (for planning, not blockers)

- No proof-of-delivery photo upload.
- No push notifications.
- List endpoints are not paginated.
- Rate limiter is in-memory (fine for one dev server; use Redis for multi-worker).
- No CI / Dockerfile / deployment config yet.
- Frontend core order flow (create → track → deliver) is not built.

---

## 5. Quick reference

```bash
# Backend (one terminal)
cd my-order-backend && source venv/bin/activate
uvicorn app.main:app --reload --port 8000
# docs: http://localhost:8000/docs

# Frontend (another terminal)
cd my_order_mobile
flutter run -t lib/main_customer.dart
```
