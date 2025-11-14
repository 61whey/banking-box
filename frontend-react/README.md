# React Frontend

Современный фронтенд на React + TypeScript для Banking Box API.

## Технологии

- **Runtime**: Bun 1.x
- **Framework**: React 18 + TypeScript
- **Build**: Vite 6
- **UI**: shadcn/ui (Radix UI + Tailwind CSS)
- **Routing**: React Router v7
- **State**: Zustand
- **HTTP**: Axios

## Быстрый старт

```bash
cd frontend-react
bun install
bun run dev  # http://localhost:5173
```

**Docker:**
```bash
docker compose up -d frontend  # http://localhost:3000
```

## Структура

```
src/
├── app/              # Страницы
│   ├── client/       # Клиентский интерфейс
│   ├── banker/       # Админ-панель банкира
│   └── developer/   # Регистрация команд
├── components/       # UI компоненты (shadcn/ui)
├── lib/             # API клиент, утилиты
├── stores/          # Zustand хранилища
└── types/           # TypeScript типы
```

## Маршруты

**Клиент** (`/app/client/*`):
- `/login` - Вход (кнопка "Войти как случайный клиент")
- `/dashboard` - Обзор (счета, транзакции, внешние банки)
- `/accounts` - Список счетов
- `/consents` - Управление согласиями
- `/transfers` - Переводы

**Банкир** (`/app/banker/*`):
- `/login` - Вход (ADMIN_USERNAME / ADMIN_PASSWORD)
- `/dashboard` - Статистика банка
- `/clients` - Список клиентов
- `/products` - Каталог продуктов
- `/monitoring` - Логи API и транзакции
- `/consents` - Управление согласиями (одобрение/отклонение)
- `/teams` - Управление командами

**Разработчик** (`/app/developer/*`):
- `/register` - Регистрация команды (также `/developer.html`)

## API

Все методы в `src/lib/api.ts`:

- `authAPI` - Авторизация (клиент, банкир, регистрация команды)
- `accountsAPI` - Счета, транзакции, внешние банки
- `consentsAPI` - Согласия клиента
- `paymentsAPI` - Переводы (автоматическое преобразование в OpenBanking формат)
- `bankerAPI` - Админ-функции банкира
- `adminAPI` - Управление командами
- `bankAPI` - Информация о банке

## Конфигурация

Переменные окружения (устанавливаются при сборке Docker):

- `VITE_API_URL` - URL бэкенда (по умолчанию: `http://localhost:54080`)
- `VITE_BANK_CODE` - Код банка

Название банка загружается динамически из API (`GET /`) и отображается в заголовках.

## Тестовые данные

**Клиенты:** `team025-1` до `team025-10`, `demo-client-001/002/003` / `password`

**Банкир:** Логин/пароль из `.env` (`ADMIN_USERNAME` / `ADMIN_PASSWORD`)

## Особенности

- Название банка из `BANK_NAME` в `.env` (динамическая загрузка)
- Поддержка светлой/темной темы
- Адаптивный дизайн
- Автоматический редирект при 401
- Совместимость со старым HTML фронтендом (работают параллельно)
- Преобразование данных из формата OpenBanking Russia v2.1 в упрощенный формат для UI
