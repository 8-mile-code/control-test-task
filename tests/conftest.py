import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.update(
    {
        "APP_NAME": "Booking Service Test",
        "DEBUG": "false",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "POSTGRES_DB": "test_bookings",
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": "postgres",
        "REDIS_URL": "redis://localhost:6379/0",
        "CELERY_BROKER_URL": "redis://localhost:6379/0",
        "CELERY_RESULT_BACKEND": "redis://localhost:6379/1",
        "BOOKING_FAILURE_RATE": "0.15",
        "BOOKING_MAX_RETRIES": "3",
        "BOOKING_RETRY_BACKOFF_SECONDS": "5",
    }
)

from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Booking  # noqa: E402, F401

TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def celery_delay_mock(mocker):
    return mocker.patch(
        "app.api.routers.bookings.process_booking_task.delay",
    )


@pytest.fixture()
def client(
    db_session: Session,
    celery_delay_mock,
) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
