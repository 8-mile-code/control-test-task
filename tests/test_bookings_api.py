from datetime import UTC, datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient


def get_valid_booking_payload() -> dict[str, str]:
    return {
        "name": "Danil",
        "datetime": "2026-06-20T15:00:00Z",
        "service_type": "consultation",
    }


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
