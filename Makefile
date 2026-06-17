.PHONY: help install dev test lint format fix check migrate revision docker-up docker-down worker

help:
	@echo "Available commands:"
	@echo "  make install      Install dependencies"
	@echo "  make dev          Run API locally"
	@echo "  make test         Run tests"
	@echo "  make lint         Run ruff linter"
	@echo "  make format       Format code"
	@echo "  make fix          Auto-fix lint issues and format code"
	@echo "  make check        Run lint and tests"
	@echo "  make migrate      Apply database migrations"
	@echo "  make revision     Create Alembic migration"
	@echo "  make docker-up    Start full stack with Docker"
	@echo "  make docker-down  Stop Docker stack"
	@echo "  make worker       Run Celery worker"

install:
	uv sync --dev

dev:
	uv run uvicorn app.main:app --reload

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

fix:
	uv run ruff check --fix .
	uv run ruff format .

check: lint test

migrate:
	uv run alembic upgrade head

revision:
	uv run alembic revision --autogenerate -m "update schema"

docker-up:
	docker compose up --build

docker-down:
	docker compose down

worker:
	uv run celery -A app.workers.celery_app.celery_app worker --loglevel=info