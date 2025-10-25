# 🏦 Bank-in-a-Box

> **Готовый шаблон банка для HackAPI 2025**  
> Создай свой собственный банк за 10 минут!

## 🎯 Что это?

**Bank-in-a-Box** — это полнофункциональный шаблон банка с OpenBanking Russia API, который ты можешь:
- Развернуть на своем сервере
- Кастомизировать под свои нужды
- Подключить к федеративной платформе HackAPI
- Использовать для разработки финтех-приложений

## ✨ Что уже реализовано

### API (42+ endpoints):
✅ **Accounts API** - счета клиентов (OpenBanking Russia v2.1)  
✅ **Account-Consents API** - управление согласиями  
✅ **Payments API** - платежи и переводы  
✅ **Products API** - финансовые продукты  
✅ **ProductAgreements API** - депозиты, кредиты, карты  
✅ **Banker API** - управление банком  
✅ **Admin API** - мониторинг и статистика  
✅ **JWKS** - федеративная авторизация RS256

### UI (9 страниц):
✅ **Client UI** - личный кабинет клиента  
✅ **Banker UI** - кабинет банкира  
✅ **Темная/светлая тема** 🌙/☀️  
✅ **Адаптивный дизайн** (Desktop/Tablet/Mobile)

### Технологии:
- **FastAPI** - современный Python web framework
- **PostgreSQL** - надежная база данных
- **SQLAlchemy** - async ORM
- **JWT** - HS256/RS256 авторизация
- **Docker** - контейнеризация

## 🚀 Быстрый старт

### Вариант 1: Docker (рекомендуется)

```bash
# 1. Клонировать репозиторий
git clone https://github.com/GalkinTech/bank-in-a-box.git
cd bank-in-a-box

# 2. Настроить конфигурацию
cp .env.example .env
# Отредактируй .env - укажи название своего банка

# 3. Запустить
docker compose up -d

# 4. Открыть UI
open http://localhost:8000/client/
```

### Вариант 2: Локально (для разработки)

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Настроить PostgreSQL
createdb mybank_db

# 3. Настроить .env
cp .env.example .env

# 4. Запустить
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## ⚙️ Кастомизация

### 1. Название и код банка

Отредактируй `.env`:
```env
BANK_CODE=mybank
BANK_NAME=My Awesome Bank
BANK_DESCRIPTION=Инновационный цифровой банк
PUBLIC_URL=http://mybank.example.com
```

### 2. Добавь свои продукты

SQL скрипт `shared/database/init.sql` содержит примеры:
```sql
INSERT INTO products (product_id, product_type, name, interest_rate, min_amount, max_amount, term_months)
VALUES 
  ('deposit-high', 'deposit', 'Премиум депозит', 12.0, 100000, 10000000, 12),
  ('loan-fast', 'loan', 'Быстрый займ', 18.0, 10000, 500000, 24);
```

### 3. Настрой ставки

Через Banker UI:
1. Открой http://localhost:8000/banker/
2. Логин: `admin` / `admin`
3. Вкладка "Products" - измени процентные ставки

### 4. Брендинг UI

Отредактируй CSS переменные в `frontend/client/theme-styles.css`:
```css
:root {
    --primary: #yourcolor;
    --bank-name: "Your Bank";
}
```

## 🔌 Подключение к федерации

Чтобы другие участники хакатона могли использовать твой банк:

### 1. Зарегистрируй банк в Directory Service

```bash
curl -X POST http://directory.hackapi.tech/banks \
  -H "Content-Type: application/json" \
  -d '{
    "bank_code": "mybank",
    "bank_name": "My Awesome Bank",
    "api_url": "https://api.mybank.com",
    "jwks_url": "https://api.mybank.com/.well-known/jwks.json"
  }'
```

### 2. Открой API для внешних запросов

В `config.py` добавь домены в CORS:
```python
allowed_origins = [
    "https://hackapi.tech",
    "http://localhost:*"
]
```

### 3. Создай RSA ключи

```bash
# Генерация ключей (уже включены в shared/keys/)
./scripts/generate_keys.sh mybank
```

## 📊 Структура проекта

```
bank-in-a-box/
├── api/                    # API endpoints
│   ├── accounts.py         # Accounts API
│   ├── consents.py         # Consents API
│   ├── payments.py         # Payments API
│   ├── products.py         # Products API
│   ├── product_agreements.py
│   ├── banker.py           # Banker API
│   ├── admin.py            # Admin API
│   ├── auth.py             # Авторизация
│   ├── well_known.py       # JWKS endpoint
│   └── ssa_registration.py # Directory регистрация
│
├── services/               # Бизнес-логика
│   ├── auth_service.py     # JWT + RS256
│   ├── consent_service.py  # Управление согласиями
│   └── payment_service.py  # Платежи и переводы
│
├── frontend/               # UI
│   ├── client/             # Client UI (5 страниц)
│   └── banker/             # Banker UI (4 страницы)
│
├── shared/                 # Общие ресурсы
│   ├── database/           # SQL init скрипты
│   └── keys/               # RSA ключи
│
├── main.py                 # FastAPI app
├── models.py               # SQLAlchemy models (16 таблиц)
├── config.py               # Конфигурация
├── database.py             # Async PostgreSQL
├── docker-compose.yml      # Docker конфигурация
├── Dockerfile              # Docker образ
├── requirements.txt        # Python зависимости
└── .env.example            # Пример конфигурации
```

## 🗄️ База данных

### Таблицы (16 шт):

1. **clients** - клиенты банка
2. **accounts** - счета клиентов
3. **transactions** - транзакции
4. **products** - финансовые продукты
5. **product_agreements** - договоры (депозиты, кредиты, карты)
6. **consents** - согласия клиентов
7. **consent_requests** - запросы на согласия
8. **payments** - платежи
9. **interbank_transfers** - межбанковские переводы
10. **bank_capital** - капитал банка
11. **bank_settings** - настройки
12. **auth_tokens** - токены авторизации
13. **notifications** - уведомления
14. **key_rate_history** - история ключевой ставки ЦБ

### Миграции

```bash
# Создать миграцию
alembic revision --autogenerate -m "описание"

# Применить миграции
alembic upgrade head
```

## 🧪 Тестирование

### 1. Через UI

Открой http://localhost:8000/client/test.html

**Тестовые клиенты:**
- `cli-mybank-001` / `password`
- `cli-mybank-002` / `password`

### 2. Через Swagger

Открой http://localhost:8000/docs

### 3. Через curl

```bash
# Авторизация
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "cli-mybank-001", "password": "password"}'

# Получить счета
curl -X GET http://localhost:8000/accounts \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📡 API Endpoints

### Auth API
- `POST /auth/login` - авторизация клиента
- `POST /auth/bank-token` - токен для межбанковских запросов
- `POST /auth/banker-login` - авторизация банкира
- `GET /auth/me` - информация о текущем пользователе

### Accounts API (OpenBanking Russia v2.1)
- `GET /accounts` - список счетов
- `GET /accounts/{accountId}` - детали счета
- `GET /accounts/{accountId}/balances` - баланс
- `GET /accounts/{accountId}/transactions` - транзакции
- `POST /accounts` - создать счет
- `DELETE /accounts/{accountId}` - закрыть счет

### Account-Consents API (OpenBanking Russia v2.1)
- `POST /account-consents/request` - запросить согласие
- `POST /account-consents/sign` - подписать согласие
- `GET /account-consents/my-consents` - мои согласия
- `GET /account-consents/requests` - запросы на согласие
- `POST /account-consents/requests/{id}/approve` - одобрить
- `POST /account-consents/requests/{id}/reject` - отклонить
- `DELETE /account-consents/{consentId}` - отозвать согласие

### Payments API
- `POST /payments` - создать платеж
- `GET /payments/{paymentId}` - статус платежа

### Products API
- `GET /products` - каталог продуктов
- `GET /products/{productId}` - детали продукта

### ProductAgreements API
- `GET /product-agreements` - список договоров
- `POST /product-agreements` - открыть продукт
- `GET /product-agreements/{agreementId}` - детали
- `DELETE /product-agreements/{agreementId}` - закрыть

### Banker API
- `GET /banker/products` - все продукты
- `PUT /banker/products/{id}` - изменить ставки
- `POST /banker/products` - создать продукт
- `GET /banker/clients` - список клиентов
- `GET /banker/consents` - запросы на согласия

### Admin API
- `GET /admin/capital` - капитал банков
- `GET /admin/stats` - статистика
- `GET /admin/transfers` - межбанковские переводы
- `GET /admin/payments` - все платежи
- `GET /admin/key-rate` - ключевая ставка ЦБ
- `POST /admin/key-rate` - установить ставку

### JWKS
- `GET /.well-known/jwks.json` - публичные ключи для RS256

## 🔐 Безопасность

### Авторизация

**Client tokens** - HS256 JWT:
```json
{
  "sub": "cli-mybank-001",
  "type": "client",
  "bank": "self"
}
```

**Bank tokens** - RS256 JWT:
```json
{
  "sub": "mybank",
  "type": "bank",
  "iss": "mybank",
  "aud": "interbank"
}
```

### Согласия (Consents)

Для межбанковских запросов требуется согласие клиента:
```http
GET /accounts?client_id=cli-001
Authorization: Bearer BANK_TOKEN
X-Consent-ID: consent-abc-123
X-Requesting-Bank: otherbank
```

## 🌐 Деплой в продакшн

### 1. На VPS/VDS

```bash
# Скопируй на сервер
scp -r bank-in-a-box/ user@server:/opt/

# Настрой nginx
sudo nano /etc/nginx/sites-available/mybank

# SSL через certbot
sudo certbot --nginx -d api.mybank.com

# Запусти
cd /opt/bank-in-a-box
docker compose up -d
```

### 2. На Kubernetes

```bash
# Создай deployment
kubectl apply -f k8s/deployment.yml

# Создай service
kubectl apply -f k8s/service.yml

# Настрой ingress
kubectl apply -f k8s/ingress.yml
```

## 🤝 Поддержка

**Документация:** [docs/](docs/)  
**Примеры:** [examples/](examples/)  
**Баг-репорты:** [Issues](https://github.com/GalkinTech/bank-in-a-box/issues)

**Основной проект:** [HackAPI 2025](https://github.com/GalkinTech/HackAPI_2025)

## 📝 Лицензия

MIT License - делай что хочешь!

## 🚀 Примеры использования

### Сценарий 1: Банк для друзей
Подними свой банк, добавь друзей как клиентов, дай им доступ к API для создания финтех-приложений.

### Сценарий 2: Нишевый банк
Создай банк для определенного сегмента (студенты, фрилансеры, IT-специалисты) с уникальными продуктами.

### Сценарий 3: Песочница
Используй для тестирования своих финтех-идей без риска.

## 💡 Идеи для кастомизации

1. **Gamification** - добавь систему достижений и бейджей
2. **AI Assistant** - интегрируй ChatGPT для консультаций
3. **Crypto** - поддержка криптовалют
4. **P2P Lending** - пиринговое кредитование
5. **Cashback** - программа лояльности
6. **API Marketplace** - продавай доступ к своему API

## 🎉 Успехов на хакатоне!

**Создано для HackAPI 2025**  
**Версия:** v1.0.0

