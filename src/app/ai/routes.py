from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.auth.dependencies import get_current_admin

from app.ai.schemas import (
    DemandForecastCreate,
    DemandForecastResponse,
    FaultDetectionCreate,
    FaultDetectionResponse,
)

from app.ai.repository import (
    create_demand_forecast,
    get_all_demand_forecasts,
    create_fault_detection,
    get_all_fault_detections,
)

router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


# ---------------------------------
# Demand Forecast APIs
# ---------------------------------

@router.post(
    "/forecast",
    response_model=DemandForecastResponse
)
def create_forecast(
    forecast: DemandForecastCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    return create_demand_forecast(db, forecast)


@router.get(
    "/forecast",
    response_model=list[DemandForecastResponse]
)
def get_forecasts(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    return get_all_demand_forecasts(db)


# ---------------------------------
# Fault Detection APIs
# ---------------------------------

@router.post(
    "/fault",
    response_model=FaultDetectionResponse
)
def create_fault(
    fault: FaultDetectionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    return create_fault_detection(db, fault)


@router.get(
    "/fault",
    response_model=list[FaultDetectionResponse]
)
def get_faults(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    return get_all_fault_detections(db)