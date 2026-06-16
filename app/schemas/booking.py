from datetime import UTC
from datetime import datetime as dt

from pydantic import BaseModel, Field, field_validator

from app.models.enums import BookingStatus
from app.schemas.base import BaseSchema


class BookingCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    datetime: dt
    service_type: str = Field(..., min_length=1, max_length=100)

    @field_validator("name", "service_type")
    @classmethod
    def validate_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field cannot be empty.")
        return value

    @field_validator("datetime")
    @classmethod
    def validate_datetime_not_in_past(cls, value: dt) -> dt:
        if value.tzinfo is None:
            raise ValueError("Datetime must include timezone.")

        if value < dt.now(UTC):
            raise ValueError("Datetime cannot be in the past.")

        return value


class BookingRead(BaseSchema):
    id: int
    name: str
    datetime: dt
    service_type: str
    status: BookingStatus
    created_at: dt
    updated_at: dt


class BookingList(BaseModel):
    items: list[BookingRead]
    total: int
    limit: int
    offset: int
