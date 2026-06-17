import logging
import random

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.booking import Booking
from app.models.enums import BookingStatus
from app.services.booking_service import BookingService
from app.services.exceptions import BookingNotFoundError
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def is_external_service_failed() -> bool:
    return random.random() < settings.BOOKING_FAILURE_RATE


def send_mock_notification(booking: Booking) -> None:
    logger.info(
        "Mock notification sent",
        extra={
            "booking_id": booking.id,
            "сustomer_name": booking.name,
            "service_type": booking.service_type,
        },
    )


@celery_app.task(name="app.workers.tasks.process_booking_task")
def process_booking_task(booking_id: int) -> None:
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
            booking, changed = service.fail_booking(db, booking_id)

            if changed:
                logger.info(
                    "Booking processing failed.",
                    extra={"booking_id": booking.id},
                )

            return

        booking, changed = service.confirm_booking(db, booking_id)

        if changed:
            logger.info(
                "Booking confirmed.",
                extra={"booking_id": booking.id},
            )
            send_mock_notification(booking)
