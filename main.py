"""
Главное FastAPI приложение банка
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

try:
    # Попытка относительного импорта (для пакетного режима)
    from .config import config
    from .database import engine
    from .models import Base
    from .middleware import APILoggingMiddleware
    from .api import (
        accounts, auth, consents, payments, admin, products, well_known, 
        banker, product_agreements, product_agreement_consents,
        product_applications, customer_leads, product_offers, product_offer_consents,
        vrp_consents, vrp_payments, interbank, payment_consents
    )
except ImportError:
    # Абсолютный импорт (для прямого запуска)
    from config import config
    from database import engine
    from models import Base
    from middleware import APILoggingMiddleware
    from api import (
        accounts, auth, consents, payments, admin, products, well_known, 
        banker, product_agreements, product_agreement_consents,
        product_applications, customer_leads, product_offers, product_offer_consents,
        vrp_consents, vrp_payments, interbank, payment_consents
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events"""
    # Startup
    print(f"🏦 Starting {config.BANK_NAME} ({config.BANK_CODE})")
    print(f"📍 Database: {config.DATABASE_URL.split('@')[1] if '@' in config.DATABASE_URL else 'local'}")
    
    # Create tables (в production использовать Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Shutdown
    print(f"🛑 Stopping {config.BANK_NAME}")
    await engine.dispose()


# Create FastAPI app
openapi_tags = [
    {"name": "🚀 Start Here", "description": "Начните отсюда — получите токен для работы с API"},
    {"name": "01 OpenBanking: Account-Consents", "description": "OpenBanking Russia v2.1 — согласия на доступ"},
    {"name": "02 OpenBanking: Accounts", "description": "OpenBanking Russia v2.1 — счета и балансы"},
    {"name": "03 OpenBanking: Payment-Consents", "description": "OpenBanking Russia — согласия на платежи"},
    {"name": "03 OpenBanking: Payments", "description": "OpenBanking Russia — разовые платежи"},
    {"name": "04 OpenBanking: VRP Consents", "description": "Согласия на периодические переводы"},
    {"name": "05 OpenBanking: VRP Payments", "description": "Периодические платежи с переменными реквизитами"},
    {"name": "06 OpenBanking: Products", "description": "Каталог банковских продуктов"},
    {"name": "07 OpenBanking: Customer Leads", "description": "Лидогенерация и управление потенциальными клиентами"},
    {"name": "08 OpenBanking: Product Offers", "description": "Персональные предложения по продуктам"},
    {"name": "09 OpenBanking: Product Offer Consents", "description": "Согласия на персональные предложения"},
    {"name": "10 OpenBanking: Product Applications", "description": "Заявки клиентов на банковские продукты"},
    {"name": "11 OpenBanking: Product Agreements", "description": "Договоры с продуктами (депозиты/кредиты/карты)"},
    {"name": "Internal: Auth", "description": "Внутренняя аутентификация (для UI банка)"},
    {"name": "Internal: Banker", "description": "Управление продуктами банка"},
    {"name": "Internal: Admin", "description": "Админ-панель и метрики"},
    {"name": "Interbank API", "description": "Межбанковские переводы (bank-to-bank)"},
    {"name": "Technical: Well-Known", "description": "JWKS — публичные ключи для проверки JWT"},
]

app = FastAPI(
    title=f"{config.BANK_NAME} API",
    description=f"""
# {config.BANK_NAME} API

OpenBanking Russia v2.1 совместимый API для разработки финансовых приложений.

## Как начать работу

**Шаг 1:** Получите токен через `POST /auth/bank-token` (раздел "🚀 Start Here")

**Шаг 2:** Используйте токен во всех запросах:
```
Authorization: Bearer <your_token>
```

**Шаг 3:** Вызывайте API (Большенство API требуют согласия для межбанковых запросов):

    """,
    version=config.API_VERSION,
    lifespan=lifespan,
    openapi_tags=openapi_tags,
    swagger_ui_parameters={"tagsSorter": "alpha", "operationsSorter": "alpha"},
    docs_url=None  # Отключаем автоматическую генерацию /docs
)

# CORS - разрешить запросы между всеми банками
# Для мультибанковых приложений нужно разрешить cross-origin запросы
allowed_origins = [
    "http://localhost:8001",  # VBank (dev)
    "http://localhost:8002",  # ABank (dev)
    "http://localhost:8003",  # SBank (dev)
    "http://localhost",       # Прокси (dev)
    "http://localhost:3000",  # Directory (dev)
    "https://vbank.open.bankingapi.ru",  # VBank (prod)
    "https://abank.open.bankingapi.ru",  # ABank (prod)
    "https://sbank.open.bankingapi.ru",  # SBank (prod)
    "https://open.bankingapi.ru",  # Landing (prod)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Все банки + прокси (dev + prod)
    allow_origin_regex=r"http://localhost:\d+",  # Разрешить localhost с любым портом для разработки команд
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add API logging middleware
app.add_middleware(APILoggingMiddleware)


# Кастомная страница Swagger
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Swagger UI"""
    return HTMLResponse(content=f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{config.BANK_NAME} API - Swagger UI</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
        window.onload = () => {{
            window.ui = SwaggerUIBundle({{
                url: '/openapi.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                tagsSorter: 'alpha',
                operationsSorter: 'alpha'
            }});
        }};
    </script>
</body>
</html>
    """)


# Include routers
app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(consents.router)
app.include_router(payment_consents.router)
app.include_router(payments.router)
app.include_router(products.router)
app.include_router(product_agreements.router)
app.include_router(product_agreement_consents.router)
app.include_router(product_applications.router)
app.include_router(customer_leads.router)
app.include_router(product_offers.router)
app.include_router(product_offer_consents.router)
app.include_router(vrp_consents.router)
app.include_router(vrp_payments.router)
app.include_router(banker.router)
app.include_router(admin.router)
app.include_router(interbank.router)
app.include_router(well_known.router)

# Mount static files (frontend)
frontend_path = Path(__file__).parent / "frontend"
if frontend_path.exists():
    app.mount("/client", StaticFiles(directory=str(frontend_path / "client"), html=True), name="client")
    app.mount("/banker", StaticFiles(directory=str(frontend_path / "banker"), html=True), name="banker")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "bank": config.BANK_NAME,
        "bank_code": config.BANK_CODE,
        "api_version": config.API_VERSION,
        "status": "online"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "bank": config.BANK_CODE,
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    # Определяем порт на основе bank_code
    port_map = {
        "vbank": 8001,
        "abank": 8002,
        "sbank": 8003
    }
    port = port_map.get(config.BANK_CODE, 8001)
    
    uvicorn.run(app, host="0.0.0.0", port=port)

