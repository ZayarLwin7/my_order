# My-Order Backend

A FastAPI-based backend for a delivery platform serving Myanmar, enabling senders to create orders, riders to fulfill deliveries, and admins to manage operations. Supports both online ordering and walk-in customers at office locations. Features comprehensive financial tracking, COD handling, multi-mode delivery, and secure authentication.

## Features

- **Multi-role Authentication**: Sender, Rider, Admin, and Staff roles with JWT-based auth
- **Walk-in Customer Support**: Office staff can create orders for customers without accounts
- **Dual Delivery Modes**: Door-to-door and bus terminal delivery options
- **Dynamic Pricing**: Quote-based pricing with item size verification and fee authorization
- **Financial Controls**: Double-entry ledger for partners, rider earnings tracking, COD handling
- **Order State Machine**: Enforced status transitions with admin override capability
- **Wallet Management**: Rider wallet with transaction logging and reconciliation
- **Dispute Handling**: 48-hour dispute window with proper financial holds
- **Security**: Rate limiting, security headers, HSTS in production, request size limits

## Tech Stack

- **Framework**: FastAPI 0.141.1
- **Database**: PostgreSQL with SQLAlchemy 2.0.51
- **Migrations**: Alembic 1.19.1
- **Authentication**: JWT (python-jose) with bcrypt password hashing
- **Testing**: pytest with httpx
- **Server**: Uvicorn with async support

## Prerequisites

- Python 3.11+
- PostgreSQL 14+
- pip and venv

## Setup

### 1. Clone and Navigate

```bash
cd /path/to/my-order-backend
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/my_order
JWT_SECRET=your-secure-random-64-character-secret-here
JWT_ALGORITHM=HS256
ENVIRONMENT=development
ALLOWED_HOSTS=localhost,127.0.0.1
ALLOWED_ORIGINS=http://localhost:3000
DELIVERY_BASE_FEE_MMK=3500
QUOTE_EXPIRE_MINUTES=30
```

**Generate a secure JWT secret:**
```bash
openssl rand -hex 32
```

### 5. Create Database

```bash
# Log into PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE my_order;
\q
```

### 6. Run Migrations

```bash
alembic upgrade head
```

This creates all necessary tables: users, riders, orders, partners, wallets, disputes, pricing, earnings, and ledgers.

### 7. Start the Server

**Development mode:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production mode:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running in development mode:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

> **Note**: API docs are disabled in production for security (`ENVIRONMENT=production`)

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user (sender/rider/admin/staff)
- `POST /api/v1/auth/login` - Login and get access token

### Orders
- `POST /api/v1/orders` - Create new order (sender only)
- `POST /api/v1/orders/walkin` - Create walk-in order (staff only, for customers without accounts)
- `PATCH /api/v1/orders/{id}/assign` - Assign order to rider (admin)
- `PATCH /api/v1/orders/{id}/verify-item-size` - Verify item size (rider)
- `PATCH /api/v1/orders/{id}/confirm-final-fee` - Confirm final fee (sender)
- `PATCH /api/v1/orders/{id}/approve-final-fee` - Admin approve fee override
- `PATCH /api/v1/orders/{id}/status` - Update order status (rider/admin)
- `PATCH /api/v1/orders/{id}/cancel` - Cancel order (sender/admin)

### Tracking
- `GET /api/v1/tracking/{order_id}` - Get order tracking history

### Riders
- `POST /api/v1/riders/apply` - Apply to become a rider
- `GET /api/v1/riders` - List all riders (admin)
- `PATCH /api/v1/riders/{user_id}/approve` - Approve rider application (admin)
- `PATCH /api/v1/riders/{user_id}/suspend` - Suspend rider (admin)

### Pricing
- `POST /api/v1/pricing/quotes` - Get delivery quote
- `GET /api/v1/pricing/item-sizes` - List item size rates
- `POST /api/v1/pricing/item-sizes` - Create item size rate (admin)

### Wallets & Finance
- `GET /api/v1/riders-wallet/balance` - Get rider wallet balance
- `GET /api/v1/riders-wallet/transactions` - List rider transactions
- `POST /api/v1/riders-wallet/remit` - Remit funds to platform (admin)
- `GET /api/v1/finance/platform-ledger` - Platform ledger entries (admin)
- `GET /api/v1/finance/partner-ledger` - Partner ledger entries (admin)

### Partners
- `POST /api/v1/partners/apply` - Apply for partner status
- `PATCH /api/v1/partners/{user_id}/approve` - Approve partner (admin)

### Disputes
- `POST /api/v1/disputes` - Create dispute
- `GET /api/v1/disputes` - List disputes
- `PATCH /api/v1/disputes/{id}/resolve` - Resolve dispute (admin)

### Rider Earnings
- `GET /api/v1/rider-earnings` - List rider earnings
- `POST /api/v1/rider-earnings/rates` - Set compensation rate (admin)
- `POST /api/v1/rider-earnings/payouts` - Create payout (admin)

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app --cov-report=html
```

Run specific test file:

```bash
pytest tests/test_security.py -v
```

## Database Migrations

### Create a new migration

```bash
alembic revision -m "description of changes"
```

### Apply migrations

```bash
alembic upgrade head
```

### Rollback one migration

```bash
alembic downgrade -1
```

### View migration history

```bash
alembic history
```

## Project Structure

```
my-order-backend/
├── alembic/                    # Database migrations
│   ├── versions/               # Migration files
│   └── env.py                  # Alembic configuration
├── app/
│   ├── routers/                # API route handlers
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── orders.py           # Order management
│   │   ├── riders.py           # Rider operations
│   │   ├── pricing.py          # Pricing and quotes
│   │   ├── tracking.py         # Order tracking
│   │   ├── riders_wallet.py    # Wallet operations
│   │   ├── partners.py         # Partner management
│   │   ├── finance.py          # Financial reporting
│   │   ├── disputes.py         # Dispute handling
│   │   └── rider_earnings.py   # Earnings and payouts
│   ├── models/                 # SQLAlchemy models
│   │   ├── user.py             # User and roles
│   │   ├── order.py            # Orders and tracking
│   │   ├── rider.py            # Rider profiles
│   │   ├── pricing.py          # Quotes and rates
│   │   ├── wallet.py           # Wallet transactions
│   │   ├── partner.py          # Partners and ledgers
│   │   ├── dispute.py          # Disputes
│   │   └── rider_earnings.py   # Earnings tracking
│   ├── schemas/                # Pydantic schemas (validation)
│   │   ├── user.py
│   │   ├── order.py
│   │   ├── finance.py
│   │   └── partner.py
│   ├── main.py                 # FastAPI app and middleware
│   ├── config.py               # Settings and environment
│   ├── database.py             # Database connection
│   ├── security.py             # Rate limiting
│   ├── auth_utils.py           # JWT and password utilities
│   └── dependencies.py         # Dependency injection
├── tests/                      # Test suite
│   ├── test_security.py
│   ├── test_auth_and_permissions.py
│   ├── test_financial_validation.py
│   ├── test_order_business_rules.py
│   └── test_pricing_validation.py
├── .env.example                # Environment template
├── .gitignore
├── alembic.ini                 # Alembic configuration
├── pytest.ini                  # Pytest configuration
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | - | Yes |
| `JWT_SECRET` | Secret key for JWT signing (min 32 chars) | - | Yes |
| `JWT_ALGORITHM` | JWT algorithm (must be HS256) | HS256 | No |
| `ENVIRONMENT` | Environment mode (development/production) | development | No |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | - | Yes (production) |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | - | No |
| `DELIVERY_BASE_FEE_MMK` | Base delivery fee in MMK | 3500 | No |
| `QUOTE_EXPIRE_MINUTES` | Quote expiration time | 30 | No |

## Security Considerations

- **JWT Secret**: Must be at least 32 characters. Generate with `openssl rand -hex 32`
- **HTTPS**: Enable HSTS in production (`ENVIRONMENT=production`)
- **Rate Limiting**: In-memory limiter (10 requests/60s on auth). Use Redis in production with multiple workers
- **CORS**: Configure `ALLOWED_ORIGINS` carefully for your Flutter frontend
- **Database**: Never commit `.env` file. Keep credentials secure
- **Admin Account**: Create first admin manually via database after initial setup

## Connecting Flutter Frontend

When integrating with Flutter:

1. **Update CORS settings** in `.env`:
   ```env
   ALLOWED_ORIGINS=http://localhost:3000,https://your-flutter-app.com
   ```

2. **API Base URL**: Point Flutter to `http://localhost:8000/api/v1` (dev) or your production domain

3. **Authentication Flow**:
   - Call `/auth/register` or `/auth/login`
   - Store `access_token` securely
   - Send token in `Authorization: Bearer <token>` header

4. **Phone Format**: Ensure Myanmar phone format consistency (+95...)

5. **Order Flow**:
   - Get quote → Create order → Rider verifies size → Sender confirms fee → Status updates

## Production Deployment Checklist

- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Use strong `JWT_SECRET` (64+ characters)
- [ ] Enable PostgreSQL connection pooling
- [ ] Set up Redis for distributed rate limiting
- [ ] Configure proper CORS origins
- [ ] Use Gunicorn/Uvicorn workers behind nginx
- [ ] Set up SSL/TLS certificates
- [ ] Enable database backups
- [ ] Configure logging and monitoring
- [ ] Create health check endpoint monitoring
- [ ] Review all security headers

## Known Limitations

- **Rate Limiter**: In-memory only. Use Redis for multi-worker deployments
- **File Uploads**: Not yet implemented (for proof of delivery photos)
- **Push Notifications**: Not implemented (consider Firebase/OneSignal)
- **Pagination**: Not yet implemented on list endpoints
- **Soft Deletes**: Hard deletes only at this stage

## Contributing

This is a private project. For questions or issues, contact the development team.

## License

Proprietary - All rights reserved

## Support

For technical support or questions about API integration, contact:
- Developer: Zayar Lwin
- Project: My-Order Platform
- Date: August 2026

---

**Built with ❤️ in Myanmar**
