from contextlib import nullcontext
from datetime import UTC, datetime
from unittest.mock import Mock

from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.enums import BookingStatus
from app.workers.tasks import process_booking_task


def create_booking_in_db(
    db_session: Session,
    *,
    status: BookingStatus = BookingStatus.PENDING,
) -> Booking:
    booking = Booking(
        name="Danil",
        datetime=datetime(2026, 6, 20, 15, 0, tzinfo=UTC),
        service_type="consultation",
        status=status.value,
    )

    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)

    return booking


def test_worker_confirms_pending_booking_and_sends_notification(
    db_session: Session,
    mocker,
) -> None:
    booking = create_booking_in_db(db_session)

    mocker.patch(
        "app.workers.tasks.SessionLocal",
        return_value=nullcontext(db_session),
    )
    mocker.patch(
        "app.workers.tasks.is_external_service_failed",
        return_value=False,
    )
    send_notification_mock: Mock = mocker.patch(
        "app.workers.tasks.send_mock_notification",
    )

    process_booking_task.run(booking.id)

    db_session.refresh(booking)

    assert booking.status == BookingStatus.CONFIRMED.value
    send_notification_mock.assert_called_once_with(booking)


def test_worker_skips_already_confirmed_booking(
    db_session: Session,
    mocker,
) -> None:
    booking = create_booking_in_db(
        db_session,
        status=BookingStatus.CONFIRMED,
    )

    mocker.patch(
        "app.workers.tasks.SessionLocal",
        return_value=nullcontext(db_session),
    )
    external_service_mock: Mock = mocker.patch(
        "app.workers.tasks.is_external_service_failed",
        return_value=False,
    )
    send_notification_mock: Mock = mocker.patch(
        "app.workers.tasks.send_mock_notification",
    )

    process_booking_task.run(booking.id)

    db_session.refresh(booking)

    assert booking.status == BookingStatus.CONFIRMED.value
    external_service_mock.assert_not_called()
    send_notification_mock.assert_not_called()


def test_worker_skips_already_failed_booking(
    db_session: Session,
    mocker,
) -> None:
    booking = create_booking_in_db(
        db_session,
        status=BookingStatus.FAILED,
    )

    mocker.patch(
        "app.workers.tasks.SessionLocal",
        return_value=nullcontext(db_session),
    )
    external_service_mock: Mock = mocker.patch(
        "app.workers.tasks.is_external_service_failed",
        return_value=False,
    )
    send_notification_mock: Mock = mocker.patch(
        "app.workers.tasks.send_mock_notification",
    )

    process_booking_task.run(booking.id)

    db_session.refresh(booking)

    assert booking.status == BookingStatus.FAILED.value
    external_service_mock.assert_not_called()
    send_notification_mock.assert_not_called()


def test_worker_skips_cancelled_booking(
    db_session: Session,
    mocker,
) -> None:
    booking = create_booking_in_db(
        db_session,
        status=BookingStatus.CANCELLED,
    )

    mocker.patch(
        "app.workers.tasks.SessionLocal",
        return_value=nullcontext(db_session),
    )
    external_service_mock: Mock = mocker.patch(
        "app.workers.tasks.is_external_service_failed",
        return_value=False,
    )
    send_notification_mock: Mock = mocker.patch(
        "app.workers.tasks.send_mock_notification",
    )

    process_booking_task.run(booking.id)

    db_session.refresh(booking)

    assert booking.status == BookingStatus.CANCELLED.value
    external_service_mock.assert_not_called()
    send_notification_mock.assert_not_called()


def test_worker_marks_pending_booking_as_failed_after_retries_exhausted(
    db_session: Session,
    mocker,
) -> None:
    booking = create_booking_in_db(db_session)

    mocker.patch(
        "app.workers.tasks.SessionLocal",
        return_value=nullcontext(db_session),
    )
    mocker.patch(
        "app.workers.tasks.is_external_service_failed",
        return_value=True,
    )
    mocker.patch(
        "app.workers.tasks.settings.BOOKING_MAX_RETRIES",
        new=0,
    )
    send_notification_mock: Mock = mocker.patch(
        "app.workers.tasks.send_mock_notification",
    )

    process_booking_task.run(booking.id)

    db_session.refresh(booking)

    assert booking.status == BookingStatus.FAILED.value
    send_notification_mock.assert_not_called()


def test_worker_repeated_run_does_not_send_notification_twice(
    db_session: Session,
    mocker,
) -> None:
    booking = create_booking_in_db(db_session)

    mocker.patch(
        "app.workers.tasks.SessionLocal",
        return_value=nullcontext(db_session),
    )
    external_service_mock: Mock = mocker.patch(
        "app.workers.tasks.is_external_service_failed",
        return_value=False,
    )
    send_notification_mock: Mock = mocker.patch(
        "app.workers.tasks.send_mock_notification",
    )

    process_booking_task.run(booking.id)
    process_booking_task.run(booking.id)

    db_session.refresh(booking)

    assert booking.status == BookingStatus.CONFIRMED.value
    assert external_service_mock.call_count == 1
    send_notification_mock.assert_called_once()
