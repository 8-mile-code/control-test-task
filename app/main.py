import logging

from fastapi import FastAPI

from app.api.routers import bookings, health
from app.core.config import settings
from app.core.logging import configure_logging

configure_logging(debug=settings.DEBUG)

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

app.include_router(health.router)
app.include_router(bookings.router)

logger.info("FastAPI application initialized...")
