# Корпоративный AI-ассистент

Чат-ассистент на базе внутренней базы знаний (RAG): ответы только по загруженным документам. Планируется доступ через веб, Telegram и MAX (VK). Сейчас реализованы backend (FastAPI), воркер (ARQ), инфраструктура и заготовки фронтенда/админки.

## Запуск

```bash
git clone https://github.com/your-org/ai-assistant.git
cd ai-assistant
cp .env.template .env   # заполнить при необходимости
docker compose up --build
```

После старта:

| Сервис        | URL                     |
|---------------|-------------------------|
| Веб-интерфейс | http://localhost        |
| Админ-панель  | http://localhost/admin  |
| API (Swagger) | http://localhost/api/docs |
| Health        | http://localhost/api/health |

## Стек

Backend: FastAPI, SQLAlchemy, Alembic, ARQ. Инфраструктура: PostgreSQL, Redis, Qdrant, MinIO. Фронтенд и админка: Vue 3, Vite. Мессенджеры: aiogram (Telegram), max-botapi-python (MAX). Прокси: Nginx. Мониторинг: Prometheus, Grafana.

## Структура

```
├── backend/          # FastAPI API + ARQ worker
├── frontend/         # Vue SPA (пользовательский чат)
├── admin/            # Vue SPA (админ-панель)
├── messengers/       # Telegram + MAX боты
├── nginx/            # nginx.dev.conf (HTTP) и nginx.conf (HTTPS)
├── prometheus/       # Конфигурация сбора метрик
├── grafana/          # Provisioning + дашборды
├── scripts/          # dev.sh, backup/
├── docs/             # restore.md, production.md, 152fz.md
├── .env.template     # Шаблон переменных окружения
└── docker-compose.yml
```
