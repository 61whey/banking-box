# 🚀 Быстрый старт Bank-in-a-Box

> **Подними свой банк за 10 минут!**

## Шаг 1: Клонировать репозиторий

```bash
git clone https://github.com/GalkinTech/bank-in-a-box.git
cd bank-in-a-box
```

## Шаг 2: Настроить конфигурацию

```bash
# Скопировать пример конфигурации
cp .env.example .env

# Отредактировать (используй любой редактор)
nano .env
```

**Обязательно измени:**
```env
BANK_CODE=mybank              # уникальный код банка
BANK_NAME=My Awesome Bank     # название
SECRET_KEY=RANDOM_STRING      # сгенерируй случайную строку!
```

## Шаг 3: Запустить

### Вариант A: Через Docker (рекомендуется)

```bash
# Запустить
docker compose up -d

# Проверить статус
docker compose ps

# Посмотреть логи
docker compose logs -f bank
```

### Вариант B: Локально (для разработки)

```bash
# Установить зависимости
pip install -r requirements.txt

# Запустить
python run.py
```

**Ожидаемый вывод:**
```
✓ Container mybank-db     Started
✓ Container mybank-api    Started
🏦 Starting My Awesome Bank (mybank)
```

## Шаг 4: Открыть UI

```bash
# Linux/Mac
open http://localhost:8000/client/

# Windows
start http://localhost:8000/client/
```

**Тестовый вход:**
- Логин: `cli-mybank-001`
- Пароль: `password`

## Шаг 5: Проверить API

### Swagger UI
```bash
open http://localhost:8000/docs
```

### curl
```bash
# Health check
curl http://localhost:8000/health

# Авторизация
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "cli-mybank-001", "password": "password"}'
```

## 🎉 Готово!

Твой банк работает на http://localhost:8000

### Что дальше?

1. **Кастомизируй** - измени продукты, ставки, брендинг
2. **Добавь клиентов** - используй SQL или Banker UI
3. **Зарегистрируй в Directory** - подключись к федерации
4. **Разрабатывай** - создавай финтех-приложения

## 📚 Полезные ссылки

- **README.md** - полная документация
- **Client UI**: http://localhost:8000/client/
- **Banker UI**: http://localhost:8000/banker/
- **API Docs**: http://localhost:8000/docs
- **JWKS**: http://localhost:8000/.well-known/jwks.json

## 🔧 Troubleshooting

### Порт 8000 занят?

Измени в `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # или любой другой
```

### База данных не запускается?

```bash
# Удалить volume и начать заново
docker compose down -v
docker compose up -d
```

### Нет тестовых клиентов?

Проверь что SQL скрипт выполнился:
```bash
docker compose exec db psql -U bankuser -d mybank_db -c "SELECT COUNT(*) FROM clients;"
```

## 💡 Полезные команды

```bash
# Остановить
docker compose down

# Перезапустить
docker compose restart

# Пересобрать после изменений
docker compose up -d --build

# Посмотреть логи
docker compose logs -f

# Подключиться к базе
docker compose exec db psql -U bankuser -d mybank_db

# Выполнить команду в контейнере
docker compose exec bank python -c "print('Hello')"
```

## 📞 Помощь

Если что-то не работает:
1. Проверь логи: `docker compose logs`
2. Проверь .env файл
3. Создай Issue: https://github.com/GalkinTech/bank-in-a-box/issues

**Удачи! 🚀**

