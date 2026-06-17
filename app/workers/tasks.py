import logging
import random

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.booking import Booking
from app.models.enums import BookingStatus
from app.services.booking_service import BookingService
from app.services.exceptions import BookingNotFoundError
from app.workers.celery_app import celery_app
from app.workers.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


def is_external_service_failed() -> bool:
    return random.random() < settings.BOOKING_FAILURE_RATE


def get_retry_countdown(retries: int) -> int:
    return settings.BOOKING_RETRY_BACKOFF_SECONDS * (2**retries)


def send_mock_notification(booking: Booking) -> None:
    logger.info(
        "Mock notification sent",
        extra={
            "booking_id": booking.id,
            "customer_name": booking.name,
            "service_type": booking.service_type,
        },
    )


@celery_app.task(
    bind=True,
    name="app.workers.tasks.process_booking_task",
    max_retries=settings.BOOKING_MAX_RETRIES,
)
def process_booking_task(self, booking_id: int) -> None:
    service = BookingService()

    with SessionLocal() as db:
        try:
            booking = service.get_booking(db, booking_id)
        except BookingNotFoundError:
            logger.info(
                "Booking not found. Task skipped.",
                extra={"booking_id": booking_id},
            )
            return

        if booking.status != BookingStatus.PENDING.value:
            logger.info(
                "Booking already processed. Task skipped.",
                extra={
                    "booking_id": booking.id,
                    "status": booking.status,
                },
            )
            return

        if is_external_service_failed():
            if self.request.retries >= settings.BOOKING_MAX_RETRIES:
                booking, changed = service.fail_booking(db, booking_id)

                if changed:
                    logger.info(
                        "Booking processing failed after retries exhausted.",
                        extra={"booking_id": booking.id},
                    )

                return

            countdown = get_retry_countdown(self.request.retries)

            logger.warning(
                "External service failed. Retrying booking task.",
                extra={
                    "booking_id": booking_id,
                    "next_retry": self.request.retries + 1,
                    "max_retries": settings.BOOKING_MAX_RETRIES,
                    "countdown": countdown,
                },
            )

            raise self.retry(
                exc=ExternalServiceError("Mock external service failed."),
                countdown=countdown,
            )

        booking, changed = service.confirm_booking(db, booking_id)

        if changed:
            logger.info(
                "Booking confirmed.",
                extra={"booking_id": booking.id},
            )
            send_mock_notification(booking)
