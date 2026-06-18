from celery import Celery

from app.core.config import settings
from app.core.logging import configure_logging

configure_logging(debug=settings.DEBUG)

celery_app = Celery(
    "booking_service",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
