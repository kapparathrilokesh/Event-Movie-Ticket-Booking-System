
from fastapi import FastAPI

from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.venues import router as venues_router
from app.routers.screens import router as screens_router
from app.routers.seats import router as seats_router
from app.routers.events import router as events_router
from app.routers.showtimes import router as showtimes_router
from app.routers.bookings import router as bookings_router
from app.routers.payments import router as payments_router
from app.routers.refunds import router as refunds_router


app = FastAPI(
    title="Event & Movie Ticket Booking System",
    version="1.0.0",
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(venues_router)
app.include_router(screens_router)
app.include_router(seats_router)
app.include_router(events_router)
app.include_router(showtimes_router)
app.include_router(bookings_router)
app.include_router(payments_router)
app.include_router(refunds_router)


@app.get("/")
async def root():
    return {
        "message": "Event & Movie Ticket Booking System API is running"
    }
