class BookingServiceError(Exception):
    """Base exception for booking service errors."""


class BookingNotFoundError(BookingServiceError):
    """Raised when booking does not exist."""


class BookingCannotBeCancelledError(BookingServiceError):
    """Raised when booking cannot be cancelled."""
