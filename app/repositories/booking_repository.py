from datetime import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.enums import BookingStatus


class BookingRepository:
    def create(
        self,
        db: Session,
        *,
        name: str,
        booking_datetime: dt,
        service_type: str,
        status: BookingStatus,
    ) -> Booking:
        booking = Booking(
            name=name,
            datetime=booking_datetime,
            service_type=service_type,
            status=status.value,
        )

        db.add(booking)
        db.flush()
        db.refresh(booking)

        return booking

    def get_by_id(
        self,
        db: Session,
        booking_id: int,
    ) -> Booking | None:
        stmt = select(Booking).where(Booking.id == booking_id)
        return db.scalar(stmt)

    def get_by_id_for_update(
        self,
        db: Session,
        booking_id: int,
    ) -> Booking | None:
        stmt = (
            select(Booking).where(Booking.id == booking_id).with_for_update()
        )
        return db.scalar(stmt)

    def get_list(
        self,
        db: Session,
        *,
        status: BookingStatus | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[Booking]:
        stmt = select(Booking).order_by(Booking.id.desc())

        if status is not None:
            stmt = stmt.where(Booking.status == status.value)

        stmt = stmt.limit(limit).offset(offset)

        return list(db.scalars(stmt).all())

    def count(
        self,
        db: Session,
        *,
        status: BookingStatus | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(Booking)

        if status is not None:
            stmt = stmt.where(Booking.status == status.value)

        return db.scalar(stmt) or 0

    def update_status(
        self,
        db: Session,
        booking: Booking,
        status: BookingStatus,
    ) -> Booking:
        booking.status = status.value

        db.add(booking)
        db.flush()
        db.refresh(booking)

        return booking
