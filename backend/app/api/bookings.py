"""Booking routes - owned by Member 3 (contract placeholder).

Doc's booking API surface:
- GET  /stations/{station_id}/available-slots
- POST /bookings/proposals
- POST /bookings/{confirmation_id}/confirm
- GET  /bookings
- GET  /bookings/{booking_reference}
- POST /bookings/{booking_reference}/cancel
"""
from fastapi import APIRouter

router = APIRouter(prefix="/bookings", tags=["bookings"])
