from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.ai.schemas import (
    DemandForecastCreate,
    DemandForecastResponse
)
from app.ai.repository import (
    create_forecast,
    get_all_forecasts
)
from app.auth.dependencies import get_current_admin

router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


# ---------------------------------
# Create Demand Forecast
# ---------------------------------

@router.post(
    "/forecast",
    response_model=DemandForecastResponse
)
def create_forecast_api(
    forecast: DemandForecastCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    return create_forecast(
        db,
        forecast
    )


# ---------------------------------
# Get All Forecasts
# ---------------------------------

@router.get(
    "/forecast",
    response_model=list[DemandForecastResponse]
)
def get_all_forecasts_api(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    return get_all_forecasts(db)