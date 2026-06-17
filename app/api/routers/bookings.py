from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.enums import BookingStatus
from app.schemas.booking import BookingCreate, BookingList, BookingRead
from app.services.booking_service import BookingService
from app.services.exceptions import (
    BookingCannotBeCancelledError,
    BookingNotFoundError,
)

router = APIRouter(prefix="/bookings", tags=["Bookings"])


def get_booking_service() -> BookingService:
    return BookingService()


DbSession = Annotated[Session, Depends(get_db)]
BookingServiceDep = Annotated[BookingService, Depends(get_booking_service)]

StatusQuery = Annotated[
    BookingStatus | None,
    Query(alias="status"),
]

LimitQuery = Annotated[int, Query(ge=1, le=100)]
OffsetQuery = Annotated[int, Query(ge=0)]


@router.post(
    "",
    response_model=BookingRead,
    status_code=status.HTTP_201_CREATED,
)
def create_booking(
    booking_data: BookingCreate,
    db: DbSession,
    service: BookingServiceDep,
) -> BookingRead:
    booking = service.create_booking(db, booking_data)

    return booking


@router.get(
    "/{booking_id}",
    response_model=BookingRead,
)
def get_booking(
    booking_id: int,
    db: DbSession,
    service: BookingServiceDep,
) -> BookingRead:
    try:
        return service.get_booking(db, booking_id)
    except BookingNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found.",
        ) from exc


@router.get(
    "",
    response_model=BookingList,
)
def list_bookings(
    db: DbSession,
    service: BookingServiceDep,
    status_filter: StatusQuery = None,
    limit: LimitQuery = 10,
    offset: OffsetQuery = 0,
) -> BookingList:
    bookings, total = service.list_bookings(
        db,
        status=status_filter,
        limit=limit,
        offset=offset,
    )

    return BookingList(
        items=bookings,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.delete(
    "/{booking_id}",
    response_model=BookingRead,
)
def cancel_booking(
    booking_id: int,
    db: DbSession,
    service: BookingServiceDep,
) -> BookingRead:
    try:
        return service.cancel_booking(db, booking_id)
    except BookingNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found.",
        ) from exc
    except BookingCannotBeCancelledError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending bookings can be cancelled.",
        ) from exc
