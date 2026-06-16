from enum import StrEnum


class BookingStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"
