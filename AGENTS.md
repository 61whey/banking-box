# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bank-in-a-Box is a full-featured banking template implementing OpenBanking Russia v2.1 API for HackAPI 2025. It provides a complete banking backend with FastAPI, PostgreSQL database, JWT authentication (HS256/RS256), and web UIs for clients and bankers.

## Development Commands

### Running the Application

**Docker (Recommended):**
```bash
# Start all services (PostgreSQL + FastAPI)
docker compose up -d

# View logs
docker compose logs -f bank

# Rebuild after code changes
docker compose up -d --build

# Stop services
docker compose down

# Stop and remove data volumes
docker compose down -v
```

**Local Development:**
```bash
# Install dependencies
pip install -r requirements.txt

# Setup PostgreSQL (ensure it's running)
createdb mybank_db

# Configure environment
cp .env.example .env
# Edit .env with your database credentials and settings

# Run development server with auto-reload
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Testing

**Manual Testing:**
```bash
# Access Swagger UI for interactive API testing
open http://localhost:8000/docs

# Test authentication
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "cli-mybank-001", "password": "password"}'

# Get accounts (use token from login response)
curl -X GET http://localhost:8000/accounts \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Running Tests:**
```bash
# Run pytest (when tests are implemented)
pytest

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -v
```

**Database Access:**
```bash
# Connect to database in Docker
docker compose exec db psql -U bankuser -d mybank_db

# Check client data
docker compose exec db psql -U bankuser -d mybank_db -c "SELECT * FROM clients;"
```

## Architecture Overview

### Application Structure

The codebase follows a layered architecture:

1. **API Layer** ([api/](api/)): FastAPI routers implementing OpenBanking Russia v2.1 endpoints
   - Each module handles a specific API domain (accounts, payments, consents, etc.)
   - Authentication handled via JWT tokens in request headers
   - Routers are included in [main.py](main.py)

2. **Service Layer** ([services/](services/)): Business logic separated from API handlers
   - `auth_service.py`: JWT token creation/verification for both HS256 (clients) and RS256 (banks)
   - `consent_service.py`: Manages consent requests and approvals for cross-bank data sharing
   - `payment_service.py`: Handles payment processing and interbank transfers

3. **Data Layer** ([models.py](models.py), [database.py](database.py)):
   - SQLAlchemy async ORM with 16+ tables
   - Key models: Client, Account, Transaction, Consent, Payment, Product, ProductAgreement
   - Database session management using AsyncSession

4. **Frontend** ([frontend/](frontend/)): Static HTML/CSS/JS
   - `client/`: Customer-facing UI (5 pages)
   - `banker/`: Administrative panel (4 pages)
   - Served via FastAPI StaticFiles

### Key Architectural Patterns

**Authentication Flow:**
- **Client Auth**: HS256 JWT tokens for customer API access (login → token → API requests)
- **Bank-to-Bank Auth**: RS256 JWT tokens signed with private keys, verified via JWKS endpoint
- Keys stored in [shared/keys/](shared/keys/)
- Token verification in [services/auth_service.py:63-91](services/auth_service.py)

**Consent Management** (Critical for cross-bank operations):
1. External bank requests consent via `POST /account-consents/request`
2. Client receives notification and reviews request
3. Client approves/rejects via `POST /account-consents/requests/{id}/approve`
4. Approved consent stored with permissions and expiration
5. External bank uses consent ID in `X-Consent-ID` header for API requests

**Payment Processing:**
- Domestic payments: Debit source account, credit destination account
- Interbank transfers: Use consent verification + bank token validation
- Payment status tracking in `payments` table

### Configuration Management

All configuration in [config.py](config.py) using pydantic-settings:
- Environment variables loaded from `.env` file
- Key settings: `BANK_CODE`, `BANK_NAME`, `DATABASE_URL`, `SECRET_KEY`
- Override defaults by editing `.env`

### Database Schema

16 main tables (see [models.py](models.py)):
- `clients`: Bank customers
- `accounts`: Customer accounts with balances
- `transactions`: Transaction history
- `products`: Financial products (deposits, loans, cards)
- `product_agreements`: Active customer agreements
- `consents` & `consent_requests`: Cross-bank data sharing
- `payments`: Payment records
- `notifications`: Customer notifications
- `auth_tokens`: Token tracking

**Note**: No Alembic migrations. Schema created via `Base.metadata.create_all()` in [main.py:30-31](main.py). For production, consider implementing Alembic migrations.

## Development Guidelines

### Adding New API Endpoints

1. Create/modify router in [api/](api/) directory
2. Import and include router in [main.py](main.py)
3. Implement business logic in [services/](services/) if complex
4. Add database models to [models.py](models.py) if needed
5. Update CORS origins in [main.py:50-56](main.py) if external access required

### Working with Authentication

- Client authentication: Use `get_current_client` dependency from [services/auth_service.py](services/auth_service.py)
- Bank authentication: Use `get_current_bank` for interbank requests
- Consent verification: Use `verify_consent` when accessing client data with external bank tokens

### Database Operations

- Always use async session: `async with get_db() as session`
- Commit explicitly: `await session.commit()`
- Refresh objects after insert: `await session.refresh(obj)`
- Use SQLAlchemy relationships for joins (defined in models)

### Testing Credentials

Default test clients (created by SQL init scripts):
- Username: `cli-mybank-001`, `cli-mybank-002`
- Password: `password`
- Banker: `admin` / `admin`

## Important Notes

- This is a hackathon template with simplified security (no OAuth 2.0 flow, direct login)
- RSA keys for RS256 are pre-generated in [shared/keys/](shared/keys/)
- Frontend uses vanilla JavaScript (no build step required)
- CORS configured for multi-bank federation in [main.py:49-64](main.py)
- The `BANK_CODE` in `.env` must match RSA key filenames (e.g., `vbank_private.pem`)

## Useful Endpoints

- Swagger docs: http://localhost:8000/docs
- Client UI: http://localhost:8000/client/
- Banker UI: http://localhost:8000/banker/
- JWKS endpoint: http://localhost:8000/.well-known/jwks.json

