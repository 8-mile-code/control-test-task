from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.enums import BookingStatus
from app.repositories.booking_repository import BookingRepository
from app.schemas.booking import BookingCreate
from app.services.exceptions import (
    BookingCannotBeCancelledError,
    BookingNotFoundError,
    BookingServiceError,
)


class BookingService:
    def __init__(self, repository: BookingRepository | None = None) -> None:
        self.repository = repository or BookingRepository()

    def create_booking(
        self,
        db: Session,
        booking_data: BookingCreate,
    ) -> Booking:
        try:
            booking = self.repository.create(
                db,
                name=booking_data.name,
                booking_datetime=booking_data.datetime,
                service_type=booking_data.service_type,
                status=BookingStatus.PENDING,
            )
            db.commit()
            db.refresh(booking)
        except Exception:
            db.rollback()
            raise

        return booking

    def get_booking(
        self,
        db: Session,
        booking_id: int,
    ) -> Booking:
        booking = self.repository.get_by_id(db, booking_id)

        if booking is None:
            raise BookingNotFoundError

        return booking

    def list_bookings(
        self,
        db: Session,
        *,
        status: BookingStatus | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[list[Booking], int]:
        bookings = self.repository.get_list(
            db,
            status=status,
            limit=limit,
            offset=offset,
        )
        total = self.repository.count(db, status=status)

        return bookings, total

    def cancel_booking(
        self,
        db: Session,
        booking_id: int,
    ) -> Booking:
        try:
            booking = self.repository.get_by_id_for_update(db, booking_id)

            if booking is None:
                raise BookingNotFoundError

            if booking.status != BookingStatus.PENDING.value:
                raise BookingCannotBeCancelledError

            booking = self.repository.update_status(
                db,
                booking,
                BookingStatus.CANCELLED,
            )

            db.commit()
            db.refresh(booking)
        except BookingServiceError:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            raise

        return booking

    def confirm_booking(
        self,
        db: Session,
        booking_id: int,
    ) -> Booking:
        try:
            booking = self.repository.get_by_id_for_update(db, booking_id)

            if booking is None:
                raise BookingNotFoundError

            if booking.status != BookingStatus.PENDING.value:
                db.rollback()
                return booking

            booking = self.repository.update_status(
                db,
                booking,
                BookingStatus.CONFIRMED,
            )

            db.commit()
            db.refresh(booking)
        except BookingServiceError:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            raise

        return booking

    def fail_booking(
        self,
        db: Session,
        booking_id: int,
    ) -> Booking:
        try:
            booking = self.repository.get_by_id_for_update(db, booking_id)

            if booking is None:
                raise BookingNotFoundError

            if booking.status != BookingStatus.PENDING.value:
                db.rollback()
                return booking

            booking = self.repository.update_status(
                db,
                booking,
                BookingStatus.FAILED,
            )

            db.commit()
            db.refresh(booking)
        except BookingServiceError:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            raise

        return booking
