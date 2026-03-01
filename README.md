# Корпоративный AI-ассистент

Корпоративный чат-ассистент на основе внутренней базы знаний (RAG).
Отвечает на вопросы сотрудников исключительно по загруженным документам.
Доступен через веб-интерфейс, Telegram и MAX (VK).

## Быстрый старт

```bash
git clone https://github.com/your-org/ai-assistant.git
cd ai-assistant
cp .env.example .env       # заполнить реальные значения
docker compose up --build
```

После запуска:

| Сервис            | URL                        |
|-------------------|----------------------------|
| Веб-интерфейс     | http://localhost            |
| Админ-панель      | http://localhost/admin      |
| API (Swagger)     | http://localhost/docs       |
| Grafana           | http://localhost:3000       |
| MinIO Console     | http://localhost:9001       |
| MailHog (письма)  | http://localhost:8025       |

Первый суперадмин создаётся автоматически из переменных `SUPERADMIN_EMAIL` и `SUPERADMIN_PASSWORD` в `.env`.

## Стек

| Слой             | Технологии                                      |
|------------------|-------------------------------------------------|
| Backend          | FastAPI, LangChain, ARQ, SQLAlchemy, Alembic    |
| LLM-провайдеры   | GigaChat, Yandex GPT, OpenRouter, VseGPT        |
| Эмбеддинги       | sentence-transformers (multilingual-e5-base)    |
| Векторная БД     | Qdrant                                          |
| База данных      | PostgreSQL                                      |
| Кэш / Очередь    | Redis + ARQ                                     |
| Хранилище файлов | MinIO (S3-совместимый)                          |
| Frontend / Admin | Vue 3, Vite, Pinia, Naive UI                    |
| Мессенджеры      | aiogram (Telegram), max-botapi-python (MAX)     |
| Прокси           | Nginx                                           |
| Мониторинг       | Prometheus + Grafana                            |
| Email (dev)      | MailHog                                         |

## Структура проекта

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
├── .env.example      # Шаблон переменных окружения
├── Makefile          # Удобные команды
└── docker-compose.yml
```

