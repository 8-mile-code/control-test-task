from datetime import datetime as dt

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.enums import BookingStatus


class Booking(TimestampMixin, Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    datetime: Mapped[dt] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    service_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=BookingStatus.PENDING.value,
        index=True,
    )
