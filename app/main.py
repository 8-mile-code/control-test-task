from fastapi import FastAPI

from app.api.routers import bookings, health
from app.core.config import settings

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

app.include_router(health.router)
app.include_router(bookings.router)
