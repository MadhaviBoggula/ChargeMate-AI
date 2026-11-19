from sqlalchemy.orm import Session

from app.ai.models import DemandForecast, FaultDetection
from app.ai.schemas import (
    DemandForecastCreate,
    FaultDetectionCreate,
)


# ---------------------------------
# Demand Forecast Repository
# ---------------------------------

def create_demand_forecast(
    db: Session,
    forecast: DemandForecastCreate
):
    new_forecast = DemandForecast(
        station_id=forecast.station_id,
        forecast_date=forecast.forecast_date,
        predicted_demand=forecast.predicted_demand,
        demand_level=forecast.demand_level,
    )

    db.add(new_forecast)
    db.commit()
    db.refresh(new_forecast)

    return new_forecast


def get_all_demand_forecasts(db: Session):
    return db.query(DemandForecast).all()


# ---------------------------------
# Fault Detection Repository
# ---------------------------------

def create_fault_detection(
    db: Session,
    fault: FaultDetectionCreate
):
    new_fault = FaultDetection(
        station_id=fault.station_id,
        connector_id=fault.connector_id,
        fault_type=fault.fault_type,
        severity=fault.severity,
        confidence=fault.confidence,
    )

    db.add(new_fault)
    db.commit()
    db.refresh(new_fault)

    return new_fault


def get_all_fault_detections(db: Session):
    return db.query(FaultDetection).all()