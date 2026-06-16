# Booking Service

Backend-сервис для записи на встречи.


## Стек

- Python 3.12
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Redis
- Celery
- Pytest
- Ruff
- Docker Compose

## Возможности

- создание брони через REST API;
- хранение брони в PostgreSQL;
- асинхронная обработка брони через Celery worker;
- смена статуса брони на `confirmed` или `failed`;
- отмена брони в статусе `pending`;
- фильтрация и пагинация списка броней;
- тесты API и worker-логики.

## Установка

```bash
uv sync --dev
```

## Локальный запуск API
```bash
make dev
```