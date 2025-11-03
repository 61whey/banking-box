# Диаграммы архитектуры банка

Эта папка содержит архитектурные диаграммы проекта Bank-in-a-Box.

## Файлы

### PlantUML исходники (редактируемые)

- **`bank-structure.puml`** - Общая структура системы (контейнеры C4)
  - Показывает: Frontend UI, Backend API, Multibank Proxy, внешние банки
  - Взаимодействие: клиенты, банкиры, разработчики

- **`bank-components.puml`** - Детальная структура компонентов (C4)
  - Показывает: API endpoints, сервисы, базу данных
  - Основные REST endpoints и их назначение

### SVG (сгенерированные)

- **`bank-structure.svg`** - Визуализация структуры
- **`bank-components.svg`** - Визуализация компонентов

## Как обновить диаграммы

### 1. Установка PlantUML

```bash
# macOS
brew install plantuml

# или через Docker
docker pull plantuml/plantuml-server
```

### 2. Редактирование

Отредактируйте `.puml` файлы в любом текстовом редакторе.

Синтаксис: [PlantUML C4 Model](https://github.com/plantuml-stdlib/C4-PlantUML)

### 3. Генерация SVG

```bash
cd docs/diagrams
plantuml -tsvg bank-structure.puml bank-components.puml
```

Или генерация PNG:
```bash
plantuml -tpng bank-structure.puml bank-components.puml
```

## Ключевые компоненты

### Frontend
- **UI Клиента** - авторизация, баланс, мультибанк
- **Кабинет банкира** - управление клиентами, продуктами, командами
- **Developer Portal** - публичная регистрация команд

### Backend API
- **Auth API** - авторизация клиентов, банкиров, регистрация команд
- **Accounts API** - управление счетами
- **Consents API** - OpenBanking согласия
- **Payments API** - платежи
- **Products API** - банковские продукты
- **Banker API** - для банкиров (клиенты, продукты, согласия)
- **Admin API** - для администраторов (команды, статистика)
- **Multibank Proxy** - проксирование запросов к внешним банкам

### Внешние системы
- **ABank** - https://abank.open.bankingapi.ru
- **VBank** - https://vbank.open.bankingapi.ru
- **SBank** - https://sbank.open.bankingapi.ru

## OpenBanking Flow

Multibank Proxy реализует полный OpenBanking Russia Flow:

1. **Bank Token** - получение токена банка (team credentials)
2. **Consent Request** - запрос согласия клиента
3. **Accounts** - получение списка счетов (с consent_id)
4. **Balances** - получение балансов (с consent_id)

## История изменений

**2025-11-03** - Обновление архитектуры:
- ✅ Добавлен Multibank Proxy
- ✅ Добавлен Developer Portal
- ✅ Добавлены внешние банки (ABank, VBank, SBank)
- ✅ Добавлен Admin API для управления командами
- ✅ Обновлен список endpoints

**2024-11-02** - Первая версия диаграмм
