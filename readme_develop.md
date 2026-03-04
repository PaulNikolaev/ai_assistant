# Developer Guide

## Структура проекта

```
ai-assistant/
├── backend/                  # FastAPI API + ARQ worker
│   ├── app/
│   │   ├── main.py           # Точка входа FastAPI, lifespan, middleware
│   │   ├── worker.py         # ARQ worker (фоновые задачи, cron)
│   │   ├── core/
│   │   │   ├── config.py     # Pydantic Settings — все настройки приложения
│   │   │   ├── database.py   # SQLAlchemy async engine, get_db dependency
│   │   │   ├── redis.py      # Redis pool, get_redis dependency
│   │   │   ├── storage.py    # MinIO S3-совместимое хранилище
│   │   │   ├── qdrant.py     # Qdrant vector DB клиент
│   │   │   ├── seed.py       # Создание суперадмина при первом запуске
│   │   │   └── models/       # SQLAlchemy ORM модели
│   │   └── api/
│   │       └── middleware/   # TraceID, логирование запросов
│   ├── alembic/              # Миграции БД
│   ├── tests/                # pytest-тесты
│   └── pyproject.toml        # Зависимости и настройки инструментов
├── frontend/                 # Vue 3 SPA (пользовательский чат)
├── admin/                    # Vue 3 SPA (админ-панель)
├── messengers/               # Telegram + MAX боты (aiogram)
├── nginx/                    # nginx.dev.conf (HTTP), nginx.conf (HTTPS)
├── prometheus/               # Конфигурация Prometheus
├── grafana/                  # Provisioning + дашборды
├── docker-compose.yml        # Dev-стек
├── docker-compose.test.yml   # Изолированный тестовый стек
├── .env.template             # Шаблон для dev
└── .env.test.template        # Шаблон для тестов
```

### Порты сервисов

| Сервис | Dev | Test |
|--------|-----|------|
| PostgreSQL | 5432 | 5433 |
| Redis | 6379 | 6380 |
| Qdrant | 6333 | 6334 |
| MinIO | 9000 | 9002 |
| Приложение (nginx) | 80 | — |

---

## Dev-окружение

### Первый запуск

```powershell
# Клонировать репозиторий
git clone https://github.com/PaulNikolaev/ai_assistant.git
cd ai-assistant

# Создать .env из шаблона и при необходимости отредактировать
cp .env.template .env

# Собрать и запустить всё
docker compose up --build
```

После старта приложение доступно:

| Интерфейс | URL |
|-----------|-----|
| Веб-чат | http://localhost |
| Админ-панель | http://localhost/admin |
| API (Swagger) | http://localhost/api/docs |
| Health | http://localhost/api/health |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |

### Обычный запуск (без пересборки)

```powershell
docker compose up -d
```

### Остановка

```powershell
# Остановить контейнеры (данные сохраняются)
docker compose stop

# Остановить и удалить контейнеры (данные сохраняются в volumes)
docker compose down

# Полный сброс вместе с данными
docker compose down -v
```

### Пересборка после изменений в коде

```powershell
docker compose up --build backend
docker compose up --build worker
```

---

## Тестовое окружение

### Первая настройка (один раз)

```powershell
# Скопировать шаблон и заполнить ENCRYPTION_KEY
cp .env.test.template .env.test

# Сгенерировать ENCRYPTION_KEY
cd backend
.venv\Scripts\python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Вставить результат в .env.test в поле ENCRYPTION_KEY
```

### Запуск тестовых сервисов

```powershell
docker compose -f docker-compose.test.yml up -d
```

Проверить что все сервисы healthy:

```powershell
docker compose -f docker-compose.test.yml ps
```

Все 4 сервиса должны показывать `(healthy)`.

### Запуск тестов

```powershell
cd backend

# Все тесты
poetry run pytest

# Подробный вывод
poetry run pytest -v

# Без отчёта покрытия (быстрее)
poetry run pytest --no-cov

# Конкретный файл
poetry run pytest tests/api/test_health.py -v

# По имени теста (подстрока)
poetry run pytest -k "test_health"

# Остановиться при первой ошибке
poetry run pytest -x

# Остановиться при первой ошибке + подробно
poetry run pytest -x -v
```

### Остановка тестовых сервисов

```powershell
# Остановить контейнеры, удалить volumes (чистое состояние для следующего запуска)
docker compose -f docker-compose.test.yml down -v

# Остановить без удаления volumes
docker compose -f docker-compose.test.yml down
```

---

## Полезные команды

### Backend — разработка

```powershell
cd backend

# Установить зависимости
poetry install

# Запустить линтер
poetry run ruff check app/

# Автоисправление lint-ошибок
poetry run ruff check app/ --fix

# Форматирование кода
poetry run black app/

# Проверить конфиг (settings загружается без ошибок)
poetry run python -c "from app.core.config import settings; print(settings.APP_ENV)"
```

### Alembic — миграции

```powershell
cd backend

# Проверить текущую ревизию
poetry run alembic current

# Создать новую миграцию
poetry run alembic revision --autogenerate -m "описание изменений"

# Применить все миграции
poetry run alembic upgrade head

# Откатить последнюю миграцию
poetry run alembic downgrade -1

# История миграций
poetry run alembic history
```

### Docker — утилиты

```powershell
# Логи конкретного сервиса
docker compose logs -f backend
docker compose logs -f worker

# Зайти в контейнер backend
docker compose exec backend bash

# Подключиться к PostgreSQL (dev)
docker compose exec postgres psql -U ai_assistant -d ai_assistant

# Подключиться к PostgreSQL (test)
docker exec $(docker compose -f docker-compose.test.yml ps -q postgres-test) `
  psql -U ai_assistant -d ai_assistant_test

# Проверить Redis (dev)
docker compose exec redis redis-cli ping

# Проверить Redis (test)
docker exec $(docker compose -f docker-compose.test.yml ps -q redis-test) redis-cli ping

# Проверить Qdrant (test)
curl http://localhost:6334/collections

# Проверить MinIO health (test)
curl http://localhost:9002/minio/health/live
```

### Health check

```powershell
# Dev
curl http://localhost/api/health

# Тест (если backend запущен локально)
curl http://localhost:8000/health
```

---

## Переменные окружения

| Файл | Назначение | В git |
|------|-----------|-------|
| `.env.template` | Шаблон для dev | Да |
| `.env` | Реальный dev-конфиг | Нет |
| `.env.test.template` | Шаблон для тестов | Да |
| `.env.test` | Реальный тестовый конфиг | Нет |

Ключевые переменные, которые нужно заполнить вручную:

- `ENCRYPTION_KEY` — Fernet-ключ, генерируется командой:
  ```powershell
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```
- `JWT_SECRET` — произвольная строка длиной от 32 символов
- `LLM_PROVIDER` / `OPENROUTER_API_KEY` / `GIGACHAT_CREDENTIALS` — в зависимости от используемого провайдера
