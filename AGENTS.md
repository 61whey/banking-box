# AGENTS.md

Banking Box - API backend implementing **OpenBanking Russia v2.1**. FastAPI + PostgreSQL with multi-bank support, consent-based data sharing, and inter-bank transfers.

**Stack:** FastAPI 0.115.0, PostgreSQL 15, SQLAlchemy 2.0.35 (async), JWT (HS256/RS256), Docker

## Code conventions

### Do

- Use venv managed by uv instead of system python.
- Before adding a new package, always check if it is already installed in the venv.
- Always use context7 when writing code, generating or debugging examples, accessing library or SDK documentation.

### Don't

- DO NOT use system python.
- DO NOT hardcode any values in the code. Use environment variables in config.py.
- DO NOT use icons or emojis in code.
- DO NOT use uppercase words if it's not necessary.
- DO NOT translate from Russian to English or vice versa. The development team is bilingual.

## Quick Start

```bash
# Local dev with hot reload
python run.py  # http://localhost:8000 | Swagger: /docs | UI: /client/

# Docker
docker compose up -d
docker compose logs -f bank

# DB rebuild (when schema changes)
docker compose down && sudo rm -rf /opt/banking-box/postgresql && docker image rm -f banking-box-bank && docker compose up -d

# Packages (using uv)
uv pip install -r requirements.txt
uv add package-name

# Testing (minimal coverage currently)
pytest
pytest tests/test_api_endpoints.py
```

## Architecture

**Three layers:** [api/](api/) (FastAPI routers) → [services/](services/) (business logic) → [models.py](models.py) (16 SQLAlchemy tables)

**Key modules:**
- Auth: [auth.py](api/auth.py), [auth_service.py](services/auth_service.py) - JWT HS256 (internal) / RS256 (inter-bank)
- Payments: [payments.py](api/payments.py), [payment_service.py](services/payment_service.py) - Internal transfers or inter-bank via `InterbankTransfer`
- Consents: [consents.py](api/consents.py), [consent_service.py](services/consent_service.py)
- Multi-bank: [multibank_proxy.py](api/multibank_proxy.py), [interbank.py](api/interbank.py)

**Auth pattern:**
- Internal: HS256 JWT with `SECRET_KEY`
- Inter-bank: RS256 JWT with keys in [shared/keys/](shared/keys/), public key at `/well-known/jwks.json`
- Headers: `Authorization: Bearer <token>`, `x-consent-id`, `x-requesting-bank`
- Passwords: bcrypt hashes stored in `clients.password_hash` and `teams.password_hash` (migration `007_add_password_hash.py`)

## Configuration

See [.env.example](.env.example). Key vars: `BANK_CODE`, `PUBLIC_URL`, `TEAM_CLIENT_ID`/`SECRET`, `SECRET_KEY`, `POSTGRES_*`, `REGISTRY_URL`

[config.py](config.py) uses Pydantic Settings.

## Key Files

- [main.py](main.py) - App init, includes all routers
- [database.py](database.py) - Async SQLAlchemy session
- [models.py](models.py) - 16 database tables
- [middleware.py](middleware.py) - API logging to `APICallLog`
- [shared/database/init.sql](shared/database/init.sql) - DB init with seed data
- [frontend/](frontend/) - Vanilla HTML/CSS/JS (no build): `/client/`, `/banker/`, `developer.html`
- [frontend-react/](frontend-react/) - React + TypeScript frontend: `/app/client/*`, `/app/banker/*`, `/app/developer/register`

## Common Tasks

**New endpoint:** Create `api/foo.py`, add logic to `services/`, include router in [main.py](main.py)

**New table:** Add to [models.py](models.py), update [init.sql](shared/database/init.sql), rebuild DB: `docker compose down -v && docker compose up -d`

**Debug:** `docker compose logs -f bank` | Swagger: `/docs` | Admin UI: `/admin`

**Frontend:**
- React frontend: `http://localhost:3000/app/` (Docker) или `http://localhost:5173/app/` (dev)
- Старый HTML frontend: `http://localhost:8001/client/` и `/banker/`
- Оба фронтенда работают параллельно, используют одинаковые API endpoints
- Название банка (`BANK_NAME` из `.env`) загружается динамически из `GET /` и отображается в заголовках
- Все API запросы преобразуют данные из формата OpenBanking Russia v2.1 в упрощенный формат для UI
- Платежи автоматически преобразуются из упрощенного формата в OpenBanking формат перед отправкой

**Docs:** [README.VTB.md](README.VTB.md) (Russian, comprehensive) | [doc/TODO.md](doc/TODO.md) | [docs/diagrams/](docs/diagrams/) | [frontend-react/README.md](frontend-react/README.md)
