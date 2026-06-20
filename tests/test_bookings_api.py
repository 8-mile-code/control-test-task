from datetime import UTC, datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.enums import BookingStatus


def get_valid_booking_payload() -> dict[str, str]:
    return {
        "name": "Danil",
        "datetime": "2030-06-20T15:00:00Z",
        "service_type": "consultation",
    }


def create_booking_via_api(
    client: TestClient,
    payload: dict[str, str] | None = None,
) -> dict:
    response = client.post(
        "/bookings",
        json=payload or get_valid_booking_payload(),
    )

    assert response.status_code == 201

    return response.json()


def test_create_booking_success(
    client: TestClient,
    celery_delay_mock: Mock,
) -> None:
    payload = get_valid_booking_payload()

    response = client.post("/bookings", json=payload)

    assert response.status_code == 201

    data = response.json()

    assert isinstance(data["id"], int)
    assert data["name"] == payload["name"]

    actual_datetime = datetime.fromisoformat(
        data["datetime"].replace("Z", "+00:00")
    )
    expected_datetime = datetime.fromisoformat(
        payload["datetime"].replace("Z", "+00:00")
    )

    if actual_datetime.tzinfo is None:
        actual_datetime = actual_datetime.replace(tzinfo=UTC)

    assert actual_datetime == expected_datetime
    assert data["service_type"] == payload["service_type"]
    assert data["status"] == "pending"
    assert "created_at" in data
    assert "updated_at" in data

    celery_delay_mock.assert_called_once_with(data["id"])


@pytest.mark.parametrize(
    "field_name",
    ["name", "datetime", "service_type"],
)
def test_create_booking_requires_mandatory_fields(
    client: TestClient,
    celery_delay_mock: Mock,
    field_name: str,
) -> None:
    payload = get_valid_booking_payload()
    payload.pop(field_name)

    response = client.post("/bookings", json=payload)

    assert response.status_code == 422
    celery_delay_mock.assert_not_called()


@pytest.mark.parametrize(
    "field_name",
    ["name", "service_type"],
)
def test_create_booking_rejects_blank_strings(
    client: TestClient,
    celery_delay_mock: Mock,
    field_name: str,
) -> None:
    payload = get_valid_booking_payload()
    payload[field_name] = "   "

    response = client.post("/bookings", json=payload)

    assert response.status_code == 422
    celery_delay_mock.assert_not_called()


def test_get_booking_by_id_success(
    client: TestClient,
    celery_delay_mock: Mock,
) -> None:
    payload = get_valid_booking_payload()

    create_response = client.post("/bookings", json=payload)

    assert create_response.status_code == 201

    created_booking = create_response.json()
    booking_id = created_booking["id"]

    celery_delay_mock.reset_mock()

    response = client.get(f"/bookings/{booking_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == booking_id
    assert data["name"] == created_booking["name"]
    assert data["datetime"] == created_booking["datetime"]
    assert data["service_type"] == created_booking["service_type"]
    assert data["status"] == created_booking["status"]
    assert data["created_at"] == created_booking["created_at"]
    assert data["updated_at"] == created_booking["updated_at"]

    celery_delay_mock.assert_not_called()


def test_get_booking_by_id_not_found(
    client: TestClient,
    celery_delay_mock: Mock,
) -> None:
    response = client.get("/bookings/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Booking not found."}

    celery_delay_mock.assert_not_called()


def test_list_bookings_success(
    client: TestClient,
    celery_delay_mock: Mock,
) -> None:
    first_booking = create_booking_via_api(client)
    second_booking = create_booking_via_api(
        client,
        {
            "name": "Alex",
            "datetime": "2030-06-21T10:00:00Z",
            "service_type": "diagnostics",
        },
    )

    celery_delay_mock.reset_mock()

    response = client.get("/bookings")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert len(data["items"]) == 2

    returned_ids = {item["id"] for item in data["items"]}

    assert returned_ids == {
        first_booking["id"],
        second_booking["id"],
    }

    celery_delay_mock.assert_not_called()


def test_list_bookings_filters_by_status(
    client: TestClient,
    db_session: Session,
    celery_delay_mock: Mock,
) -> None:
    pending_booking = create_booking_via_api(client)
    confirmed_booking = create_booking_via_api(
        client,
        {
            "name": "Alex",
            "datetime": "2030-06-21T10:00:00Z",
            "service_type": "diagnostics",
        },
    )

    booking = db_session.scalar(
        select(Booking).where(Booking.id == confirmed_booking["id"])
    )
    assert booking is not None

    booking.status = BookingStatus.CONFIRMED.value
    db_session.commit()

    celery_delay_mock.reset_mock()

    response = client.get("/bookings?status=confirmed")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == confirmed_booking["id"]
    assert data["items"][0]["status"] == "confirmed"

    returned_ids = {item["id"] for item in data["items"]}

    assert pending_booking["id"] not in returned_ids

    celery_delay_mock.assert_not_called()


def test_list_bookings_supports_pagination(
    client: TestClient,
    celery_delay_mock: Mock,
) -> None:
    create_booking_via_api(
        client,
        {
            "name": "First",
            "datetime": "2030-06-20T10:00:00Z",
            "service_type": "consultation",
        },
    )
    second_booking = create_booking_via_api(
        client,
        {
            "name": "Second",
            "datetime": "2030-06-21T10:00:00Z",
            "service_type": "consultation",
        },
    )
    create_booking_via_api(
        client,
        {
            "name": "Third",
            "datetime": "2030-06-22T10:00:00Z",
            "service_type": "consultation",
        },
    )

    celery_delay_mock.reset_mock()

    response = client.get("/bookings?limit=1&offset=1")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert data["limit"] == 1
    assert data["offset"] == 1
    assert len(data["items"]) == 1

    returned_id = data["items"][0]["id"]

    assert returned_id == second_booking["id"]
    celery_delay_mock.assert_not_called()


def test_cancel_pending_booking_success(
    client: TestClient,
    celery_delay_mock: Mock,
) -> None:
    booking = create_booking_via_api(client)

    celery_delay_mock.reset_mock()

    response = client.delete(f"/bookings/{booking['id']}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == booking["id"]
    assert data["status"] == "cancelled"
    assert data["name"] == booking["name"]
    assert data["service_type"] == booking["service_type"]

    celery_delay_mock.assert_not_called()


def test_cancel_confirmed_booking_returns_409(
    client: TestClient,
    db_session: Session,
    celery_delay_mock: Mock,
) -> None:
    booking = create_booking_via_api(client)

    db_booking = db_session.scalar(
        select(Booking).where(Booking.id == booking["id"])
    )
    assert db_booking is not None

    db_booking.status = BookingStatus.CONFIRMED.value
    db_session.commit()

    celery_delay_mock.reset_mock()

    response = client.delete(f"/bookings/{booking['id']}")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Only pending bookings can be cancelled."
    }

    celery_delay_mock.assert_not_called()


def test_cancel_failed_booking_returns_409(
    client: TestClient,
    db_session: Session,
    celery_delay_mock: Mock,
) -> None:
    booking = create_booking_via_api(client)

    db_booking = db_session.scalar(
        select(Booking).where(Booking.id == booking["id"])
    )
    assert db_booking is not None

    db_booking.status = BookingStatus.FAILED.value
    db_session.commit()

    celery_delay_mock.reset_mock()

    response = client.delete(f"/bookings/{booking['id']}")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Only pending bookings can be cancelled."
    }

    celery_delay_mock.assert_not_called()


def test_cancel_missing_booking_returns_404(
    client: TestClient,
    celery_delay_mock: Mock,
) -> None:
    response = client.delete("/bookings/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Booking not found."}

    celery_delay_mock.assert_not_called()


def test_cancel_already_cancelled_booking_returns_409(
    client: TestClient,
    celery_delay_mock: Mock,
) -> None:
    booking = create_booking_via_api(client)

    first_response = client.delete(f"/bookings/{booking['id']}")

    assert first_response.status_code == 200
    assert first_response.json()["status"] == "cancelled"

    celery_delay_mock.reset_mock()

    second_response = client.delete(f"/bookings/{booking['id']}")

    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Only pending bookings can be cancelled."
    }

    celery_delay_mock.assert_not_called()
