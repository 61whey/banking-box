# AGENTS.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Banking API Backend** implementing **OpenBanking Russia v2.1** specification. Built with FastAPI and PostgreSQL, it provides a complete banking system with multi-bank support, consent-based data sharing, and inter-bank transfers.

**Tech Stack:** FastAPI 0.115.0, PostgreSQL 15, SQLAlchemy 2.0.35 (async), JWT authentication (HS256/RS256), Docker

## Essential Development Commands

### Running the Application

**Local Development (Hot Reload):**
```bash
python run.py
# Starts on http://localhost:8000
# Swagger UI: http://localhost:8000/docs
# Client UI: http://localhost:8000/client/
```

**Docker Development:**
```bash
# Start all services (DB + API)
docker compose up -d

# View logs
docker compose logs -f bank

# Fast rebuild (nuclear option when DB schema changes)
docker compose down
sudo rm -rf /opt/banking-box/postgresql
docker image rm -f banking-box-bank
docker compose up -d
```

### Package Management

Uses `uv` (modern Python package manager):
```bash
# Install dependencies
uv pip install -r requirements.txt

# Add new dependency (updates pyproject.toml and uv.lock)
uv add package-name

# Sync from pyproject.toml
uv sync
```

**Note:** Migration from `requirements.txt` to `uv` is ongoing. Currently both files exist.

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api_endpoints.py

# Run tests matching pattern
pytest -k "test_accounts"

# Verbose output
pytest -v
```

**Current test coverage is minimal.** Only `tests/test_api_endpoints.py` exists with basic product endpoint tests.

### Database Operations

```bash
# Connect to database container
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB

# Reset database (WARNING: destroys all data)
docker compose down -v
docker compose up -d
```

**Database initialization:** Uses `shared/database/init.sql` run at container startup. **TODO:** Migrate to Alembic for version-controlled migrations.

### Linting/Formatting

**No linting tools currently configured.** Consider adding ruff, black, or mypy if needed.

## Architecture Overview

### Three-Layer Architecture

```
API Layer (api/*) → Service Layer (services/*) → Database (models.py)
```

**API Layer** ([api/](api/)) - 19 FastAPI router modules implementing OpenBanking Russia v2.1 endpoints:
- Authentication: [auth.py](api/auth.py) - JWT-based login for clients/bankers/teams
- Account Access: [accounts.py](api/accounts.py) - Account data with consent checking
- Consents: [consents.py](api/consents.py) - Consent lifecycle management
- Payments: [payments.py](api/payments.py) - Payment initiation and status
- Products: [products.py](api/products.py), [product_agreements.py](api/product_agreements.py), [product_applications.py](api/product_applications.py), [product_offers.py](api/product_offers.py)
- VRP (Variable Recurring Payments): [vrp_consents.py](api/vrp_consents.py), [vrp_payments.py](api/vrp_payments.py)
- Multi-bank: [multibank_proxy.py](api/multibank_proxy.py) - Aggregate accounts from other banks
- Inter-bank: [interbank.py](api/interbank.py) - Handle transfers between banks
- Internal: [banker.py](api/banker.py), [admin.py](api/admin.py) - Management interfaces

**Service Layer** ([services/](services/)) - Reusable business logic:
- [auth_service.py](services/auth_service.py) - JWT creation (HS256/RS256), token verification, JWKS fetching
- [consent_service.py](services/consent_service.py) - Consent validation, auto-approval logic
- [payment_service.py](services/payment_service.py) - Payment processing, internal vs inter-bank routing

**Data Layer** ([models.py](models.py)) - 16 SQLAlchemy tables:
- Core: `Client`, `Account`, `Transaction`, `Team`
- Products: `Product`, `ProductAgreement`
- Consents: `Consent`, `ConsentRequest`, `PaymentConsent`, `PaymentConsentRequest`
- Payments: `Payment`, `InterbankTransfer`
- System: `BankSettings`, `BankCapital`, `AuthToken`, `Notification`, `KeyRateHistory`, `APICallLog`

### Request Flow Patterns

**Internal Client Request:**
```
Client UI → API endpoint → verify JWT (HS256) → Service layer → Database → Response
```

**Inter-Bank Request (external bank accessing our data):**
```
External Bank → API endpoint
  → detect x-requesting-bank header
  → verify JWT (RS256 with their public key)
  → ConsentService.check_consent()
  → Database → Response
```

**Payment Flow:**
```
POST /payments → PaymentService.initiate_payment()
  → Check balance
  → IF to_account in same bank:
      → Transfer funds directly
      → Status: "AcceptedSettlementCompleted"
    ELSE:
      → Create InterbankTransfer
      → Deduct from BankCapital
      → Status: "AcceptedSettlementInProcess"
```

### Authentication Patterns

**Two JWT algorithms:**
1. **HS256** - Internal clients (symmetric key from `SECRET_KEY` env var)
2. **RS256** - Inter-bank requests (asymmetric keys in `shared/keys/`)

**Current authentication TODOs:**
- Password verification is plain text comparison (see [auth.py:68-69](api/auth.py#L68-L69))
- No authentication on `/client/*`, `/banker/*`, `/admin/*` UI endpoints
- Passwords in `shared/database/init.sql:221` are plain text

## Configuration

**Environment variables** (see [.env.example](.env.example)):
- `BANK_CODE` - Unique bank identifier (e.g., "vbank")
- `BANK_NAME`, `BANK_DESCRIPTION` - Display names
- `PUBLIC_URL` - Public API URL for inter-bank communication
- `TEAM_CLIENT_ID`, `TEAM_CLIENT_SECRET` - Hackathon team credentials
- `SECRET_KEY` - JWT signing key (HS256)
- `POSTGRES_*` - Database configuration
- `REGISTRY_URL` - Directory service for bank discovery

**Loading:** [config.py](config.py) uses Pydantic Settings with `.env` file support.

## Frontend Structure

Located in [frontend/](frontend/) - vanilla HTML/CSS/JS (no build step required):
- `/client/` - Customer dashboard with multi-bank account aggregation
- `/banker/` - Bank administration interface
- `developer.html` - Public team registration portal

**Theming:** CSS variables in `theme-styles.css` with dark/light mode toggle.

## OpenBanking Russia v2.1 Compliance

All API responses follow the specification format:
```json
{
  "Data": { /* actual data */ },
  "Links": {
    "Self": "https://...",
    "First": "https://...",
    "Last": "https://..."
  },
  "Meta": {
    "TotalPages": 1
  }
}
```

**Key headers for inter-bank requests:**
- `Authorization: Bearer <RS256_JWT>`
- `x-consent-id: <consent_id>`
- `x-requesting-bank: <bank_code>`

**JWKS endpoint:** [/well-known/jwks.json](api/well_known.py) provides RS256 public key for other banks.

## Key Files

- [main.py](main.py) - FastAPI app initialization, CORS, middleware, router includes
- [run.py](run.py) - Development server launcher
- [config.py](config.py) - Configuration management
- [database.py](database.py) - Async SQLAlchemy session factory
- [models.py](models.py) - Database schema (16 tables)
- [middleware.py](middleware.py) - API request logging to `APICallLog` table
- [shared/database/init.sql](shared/database/init.sql) - Database initialization and seed data
- [shared/keys/](shared/keys/) - RSA key pairs for RS256 JWT signing

## Documentation

- [README.VTB.md](README.VTB.md) - Comprehensive Russian documentation (571 lines)
  - Architecture diagrams, API examples, deployment guides
- [doc/TODO.md](doc/TODO.md) - Technical debt tracking
- [docs/diagrams/](docs/diagrams/) - PlantUML architecture diagrams (.puml + .svg)
  - `bank-structure.svg` - System overview
  - `bank-components.svg` - Component diagram
  - `database-schema.svg` - ER diagram

## Common Development Scenarios

**Adding a new API endpoint:**
1. Create router in `api/new_endpoint.py`
2. Add business logic to appropriate service in `services/`
3. Include router in [main.py](main.py): `app.include_router(new_endpoint.router)`

**Adding a database table:**
1. Add model to [models.py](models.py)
2. Update [shared/database/init.sql](shared/database/init.sql) OR create Alembic migration (preferred, see TODO)
3. Rebuild database: `docker compose down -v && docker compose up -d`

**Testing inter-bank communication:**
1. Get team token: `POST /auth/team-token` with `TEAM_CLIENT_ID`/`SECRET`
2. Use token in `Authorization: Bearer <token>` header
3. Include `x-consent-id` and `x-requesting-bank` headers

**Debugging:**
- Check API logs: `docker compose logs -f bank`
- View API call history: Query `APICallLog` table or use `/admin` interface
- Swagger UI: `http://localhost:8000/docs` for interactive testing
