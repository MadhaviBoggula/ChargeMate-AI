from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.station import Station
from app.models.user import User
from app.schemas.station import StationResponse


router = APIRouter()


@router.get("", response_model=list[StationResponse])
def list_stations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all active charging stations."""

    statement = (
        select(Station)
        .where(Station.is_active.is_(True))
        .order_by(Station.name.asc())
    )

    return db.scalars(statement).all()