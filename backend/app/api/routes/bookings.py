from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_driver_id
from app.database.session import get_db
from app.schemas.booking import (
    BookingOut,
    BookingProposalCreate,
    BookingProposalOut,
)
from app.services import booking_service

router = APIRouter()


@router.post(
    "/proposals",
    response_model=BookingProposalOut,
    status_code=status.HTTP_201_CREATED,
)
def create_proposal(
    payload: BookingProposalCreate,
    driver_id: UUID = Depends(get_driver_id),
    db: Session = Depends(get_db),
):
    """Prepare a booking summary without reserving the slot."""

    proposal = booking_service.prepare_booking(db, driver_id, payload)

    return BookingProposalOut(
        confirmation_id=proposal.id,
        expires_at=proposal.expires_at,
        summary=proposal.summary,
    )


@router.post(
    "/{confirmation_id}/confirm",
    response_model=BookingOut,
    status_code=status.HTTP_201_CREATED,
)
def confirm_proposal(
    confirmation_id: UUID,
    driver_id: UUID = Depends(get_driver_id),
    db: Session = Depends(get_db),
):
    """Revalidate availability and create the booking."""

    booking = booking_service.confirm_booking(db, driver_id, confirmation_id)

    return booking_service.booking_payload(booking)


@router.get("", response_model=list[BookingOut])
def list_bookings(
    booking_status: str | None = Query(
        default=None,
        alias="status",
        pattern="^(CONFIRMED|CANCELLED|COMPLETED|EXPIRED)$",
    ),
    station_id: UUID | None = None,
    upcoming_only: bool = False,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    driver_id: UUID = Depends(get_driver_id),
    db: Session = Depends(get_db),
):
    """List the authenticated driver's bookings."""

    bookings = booking_service.list_bookings(
        db,
        driver_id,
        status=booking_status,
        station_id=station_id,
        upcoming_only=upcoming_only,
        skip=skip,
        limit=limit,
    )

    return [booking_service.booking_payload(item) for item in bookings]


@router.get("/{booking_reference}", response_model=BookingOut)
def get_booking(
    booking_reference: str,
    driver_id: UUID = Depends(get_driver_id),
    db: Session = Depends(get_db),
):
    """Return one of the authenticated driver's bookings."""

    booking = booking_service.get_booking(
        db,
        driver_id,
        booking_reference,
    )

    return booking_service.booking_payload(booking)


@router.post("/{booking_reference}/cancel", response_model=BookingOut)
def cancel_booking(
    booking_reference: str,
    driver_id: UUID = Depends(get_driver_id),
    db: Session = Depends(get_db),
):
    """Cancel an eligible upcoming booking."""

    booking = booking_service.cancel_booking(
        db,
        driver_id,
        booking_reference,
    )

    return booking_service.booking_payload(booking)
