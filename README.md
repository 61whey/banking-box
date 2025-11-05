# Banking box


## Overview


## Quick Start

```bash
# Start with Docker
docker compose up -d

# Remove existing container and data
sudo rm -rf /opt/banking-box/ && docker compose down && docker compose up -d

# Access services
open http://localhost:8000/client/    # Client UI
open http://localhost:8000/banker/    # Banker UI
open http://localhost:8000/docs       # API Documentation
```

## Project Structure

```
banking-box/
│
├── api/                          # API Layer - FastAPI routers (used by main.py)
│   ├── __init__.py
│   ├── accounts.py               # /accounts               - account data & balances
│   ├── admin.py                  # /admin/*                - statistics, capital, monitoring
│   ├── auth.py                   # /auth/login             - client/bank authentication
│   ├── banker.py                 # /banker/*               - bank management endpoints
│   ├── consents.py               # /account-consents       - consent management
│   ├── customer_leads.py         # /customer-leads         - lead generation API
│   ├── payments.py               # /payments               - payment processing
│   ├── product_agreements.py     # /product-agreements     - deposits/loans/cards
│   ├── product_applications.py   # /product-applications   - product applications
│   ├── product_offer_consents.py # /product-offer-consents - consent for offers
│   ├── product_offers.py         # /product-offers         - personalized offers
│   ├── products.py               # /products               - product catalog
│   ├── vrp_consents.py           # /vrp-consents           - variable recurring payments
│   ├── vrp_payments.py           # /vrp-payments           - VRP payment execution
│   └── well_known.py             # /.well-known/jwks.json  - RS256 public keys
│
├── services/                     # Business Logic Layer (used by API routers)
│   ├── auth_service.py           # JWT creation/verification (HS256/RS256)
│   │                             # - create_access_token() - used by auth.py
│   │                             # - verify_token()        - used by all protected endpoints
│   │                             # - get_current_client()  - dependency for client auth
│   │                             # - get_current_bank()    - dependency for bank-to-bank
│   │
│   ├── consent_service.py        # Consent verification for cross-bank requests
│   │                             # - verify_consent()    - used by accounts.py, payments.py
│   │                             # - check_permissions() - validates consent scope
│   │
│   └── payment_service.py        # Payment processing logic
│                                 # - process_payment() - used by payments.py
│                                 # - process_interbank_transfer() - cross-bank payments
│
├── frontend/                     # Static Web UI (served by main.py via StaticFiles)
│   ├── client/                   # Customer-facing UI (mounted at /client)
│   │   ├── index.html            # Login page
│   │   ├── dashboard.html        # Account overview, balance, transactions
│   │   ├── consents.html         # Consent requests & approvals
│   │   ├── test.html             # API testing interface
│   │   └── theme-switcher.js     # Theme toggle logic
│   │
│   ├── banker/                   # Administrative UI (mounted at /banker)
│   │   ├── index.html            # Banker login
│   │   ├── clients.html          # Client management
│   │   ├── products.html         # Product & interest rate management
│   │   ├── consents.html         # Consent request approvals
│   │   └── monitoring.html       # Bank statistics & monitoring
│   │
│   └── components/               # Reusable UI components
│       └── bank-switcher.html    # Multi-bank selector widget
│
├── shared/                       # Shared resources (used by Docker & services)
│   ├── database/                 # SQL initialization scripts
│   │   ├── init-vbank.sql        # Test data for Virtual Bank
│   │   ├── init-abank.sql        # Test data for Alpha Bank
│   │   └── init-sbank.sql        # Test data for Sigma Bank
│   │                             # Mounted in docker-compose.yml at db service
│   │
│   └── keys/                     # RSA keypairs for RS256 JWT (used by auth_service.py)
│       ├── vbank_private.pem     # Virtual Bank signing key
│       ├── vbank_public.pem      # Virtual Bank verification key
│       ├── vbank_jwks.json       # JWKS format for well_known.py endpoint
│       ├── abank_*.pem           # Alpha Bank keys
│       ├── abank_jwks.json
│       ├── sbank_*.pem           # Sigma Bank keys
│       └── sbank_jwks.json
│
├── doc/                          # Documentation
│   ├── README.org.md             # Original README
│   ├── QUICKSTART.org.md         # Original Quick start guide
│
├── main.py                       # FastAPI Application Entry Point
├── models.py                     # SQLAlchemy ORM Models (used by all API/services)
├── database.py                   # Database Connection & Session Management
├── config.py                     # Configuration Management (used by all modules)
├── docker-compose.yml            
├── Dockerfile                    
├── requirements.txt              # old, original 
│
├── AGENTS.md                     # Claude/Cursor/Gemini/Codex AI Assistant Guide
│                                 # You can and should update it to your needs!
```

## Architecture

### Component Flow

```
Client/Banker UI (frontend/)
        ↓
API Routers (api/)
        ↓
Business Logic (services/)
        ↓
ORM Models (models.py)
        ↓
PostgreSQL Database
```

### API Layer (`api/`)

FastAPI routers implementing OpenBanking Russia v2.1 endpoints. Each module handles a specific domain:

- **accounts.py**: Account information, balances, transactions
- **consents.py**: Consent requests & approvals for cross-bank data sharing
- **payments.py**: Payment initiation & status
- **products.py**: Financial product catalog
- **product_agreements.py**: Customer agreements (deposits, loans, cards)
- **auth.py**: Authentication (login, token generation)
- **banker.py**: Bank management operations
- **admin.py**: Monitoring & statistics

All routers are included in `main.py` and use dependencies from `services/`.

### Service Layer (`services/`)

Business logic separated from API handlers:

- **auth_service.py**:
  - Token generation (HS256 for clients, RS256 for banks)
  - Token verification with JWKS support
  - Authentication dependencies (`get_current_client`, `get_current_bank`)

- **consent_service.py**:
  - Consent verification for cross-bank requests
  - Permission scope validation
  - Used by all endpoints that handle external bank requests

- **payment_service.py**:
  - Payment processing logic
  - Interbank transfer coordination
  - Balance updates & transaction recording

### Data Layer (`models.py`, `database.py`)

- **models.py**: 16+ SQLAlchemy models with relationships
- **database.py**: Async PostgreSQL connection & session management
- All API endpoints use `get_db()` dependency for database access

### Frontend (`frontend/`)

Static HTML/CSS/JS served via FastAPI `StaticFiles`:

- **client/**: Customer portal (login, dashboard, consents)
- **banker/**: Administrative panel (client mgmt, products, monitoring)
- No build step required - vanilla JavaScript


# Run development server
python -m uvicorn main:app --reload
```

### Running with Docker

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f bank

# Rebuild after changes
docker compose up -d --build
```

### Testing

```bash
# API documentation
open http://localhost:8000/docs

# Manual testing
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "cli-mybank-001", "password": "password"}'

# Run tests (when implemented)
pytest
```

### Database Access

```bash
# Connect to PostgreSQL
docker compose exec db psql -U bankuser -d mybank_db

# Check tables
\dt

# Query clients
SELECT * FROM clients;
```

## Federation & Directory Service

This bank can participate in a multi-bank federation:

1. **Register** your bank in Directory Service
2. **Publish** JWKS endpoint at `/.well-known/jwks.json`
3. **Accept** cross-bank requests with RS256 tokens
4. **Verify** consent before sharing client data

See [doc/federated_architecture.md](doc/federated_architecture.md) for details.

## API Endpoints

[API Endpoints](doc/API.md)

## Key Files Explained

| File | Used By | Purpose |
|------|---------|---------|
| `main.py` | uvicorn | FastAPI app initialization, router registration |
| `config.py` | All modules | Configuration management via environment variables |
| `models.py` | All API/services | Database schema & ORM relationships |
| `database.py` | All API endpoints | Database connection & session factory |
| `api/*.py` | main.py | HTTP endpoint handlers, request/response logic |
| `services/*.py` | api/*.py | Business logic, reusable across endpoints |
| `shared/keys/*.pem` | auth_service.py | RSA keypairs for bank-to-bank JWT signing |
| `shared/database/*.sql` | docker-compose.yml | Initial database seeding with test data |
| `frontend/**/*.html` | main.py (StaticFiles) | Web UI served at /client and /banker |

