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

## Retry и backoff

Celery worker имитирует вызов внешнего сервиса при обработке брони.

Вероятность сбоя настраивается переменной:

```env
BOOKING_FAILURE_RATE=0.15
BOOKING_MAX_RETRIES=3
BOOKING_RETRY_BACKOFF_SECONDS=5
```
Если внешний сервис временно недоступен, задача повторяется с экспоненциальным backoff.

Задержка считается по формуле:

```bash
BOOKING_RETRY_BACKOFF_SECONDS * 2^retry_number
```

Например, при `BOOKING_RETRY_BACKOFF_SECONDS=5` повторы будут примерно через 5, 10, 20 секунд.
Если все попытки исчерпаны, бронь переводится в статус failed.

Повторный запуск задачи идемпотентен: worker меняет только брони в статусе pending. Брони в статусах confirmed, failed и cancelled повторно не обрабатываются.
