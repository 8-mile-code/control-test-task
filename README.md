# Booking Service

Backend-сервис для записи на встречи.

Пользователь создаёт бронь через REST API, бронь сохраняется в PostgreSQL со
статусом `pending`, после чего Celery worker асинхронно обрабатывает задачу и
переводит бронь в `confirmed` или `failed`.

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
- retry с экспоненциальным backoff при сбое внешнего сервиса;
- отмена брони только в статусе `pending`;
- фильтрация и пагинация списка броней;
- идемпотентная обработка Celery-задач;
- структурированные JSON-логи приложения.

## Быстрый запуск через Docker

Создайте `.env` на основе примера:

```bash
cp .env.example .env
```

Запустите весь стек:

```bash
make docker-up
```

Или напрямую:

```bash
docker compose up --build
```

API будет доступен по адресу:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Миграции применяются автоматически при старте `api` контейнера.

## API endpoints

- `GET /health` — healthcheck
- `POST /bookings` — создать бронь
- `GET /bookings/{id}` — получить бронь по id
- `GET /bookings?status=pending&limit=10&offset=0` — получить список броней
- `DELETE /bookings/{id}` — отменить бронь в статусе `pending`

## Пример создания брони

```bash
curl -X POST http://127.0.0.1:8000/bookings \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Danil",
    "datetime": "2030-06-25T15:00:00Z",
    "service_type": "consultation"
  }'
```

Сразу после создания бронь возвращается со статусом `pending`.
После этого Celery worker асинхронно переводит её в `confirmed` или `failed`.

## Локальная разработка

Установить зависимости:

```bash
uv sync --dev
```

Поднять PostgreSQL и Redis:

```bash
docker compose up -d postgres redis
```

Применить миграции:

```bash
make migrate
```

Запустить API:

```bash
make dev
```

Запустить Celery worker:

```bash
make worker
```

## Команды

```bash
make dev        # запустить API локально
make worker     # запустить Celery worker локально
make migrate    # применить миграции
make lint       # проверить код Ruff
make format     # отформатировать код
make fix        # автоисправления Ruff и форматирование
make test       # запустить тесты
make docker-up  # запустить весь стек через Docker
make docker-down # остановить Docker-стек
```

## Тесты

Тесты запускаются из корня проекта:

```bash
make test
```

Или напрямую:

```bash
uv run pytest
```

Для тестов используется SQLite in-memory. FastAPI dependency для database
session переопределяется, а отправка Celery-задачи мокается, поэтому для
запуска тестов не требуются PostgreSQL, Redis, Celery worker или Docker.

API-тесты покрывают:

- создание и валидацию брони;
- получение брони по id;
- получение списка, фильтрацию и пагинацию;
- отмену брони и запрещённые переходы статусов.

## Retry и backoff

Celery worker имитирует вызов внешнего сервиса при обработке брони.

Вероятность сбоя настраивается переменной:

```env
BOOKING_FAILURE_RATE=0.15
```

Если внешний сервис временно недоступен, задача повторяется с
экспоненциальным backoff.

Настройки:

```env
BOOKING_MAX_RETRIES=3
BOOKING_RETRY_BACKOFF_SECONDS=5
```

Задержка считается по формуле:

```text
BOOKING_RETRY_BACKOFF_SECONDS * 2^retry_number
```

Например, при `BOOKING_RETRY_BACKOFF_SECONDS=5` повторы будут примерно через
`5`, `10`, `20` секунд.

Если все попытки исчерпаны, бронь переводится в статус `failed`.

## Идемпотентность

Celery-задача меняет только брони в статусе `pending`.

Повторный запуск задачи безопасен:

```text
pending   -> confirmed или failed
confirmed -> без изменений
failed    -> без изменений
cancelled -> без изменений
```

Mock-уведомление логируется только при успешном переходе `pending` ->
`confirmed` и не отправляется повторно при повторном запуске задачи.

## Статусы брони

- `pending` — бронь создана и ожидает обработки worker-ом
- `confirmed` — бронь успешно подтверждена
- `failed` — обработка завершилась ошибкой
- `cancelled` — бронь отменена пользователем
