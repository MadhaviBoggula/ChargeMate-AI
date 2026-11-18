from sqlalchemy.orm import Session

from app.ai.models import DemandForecast


# ---------------------------------
# Create Demand Forecast
# ---------------------------------

def create_forecast(
    db: Session,
    forecast
):

    new_forecast = DemandForecast(
        station_id=forecast.station_id,
        forecast_date=forecast.forecast_date,
        predicted_demand=forecast.predicted_demand,
        demand_level=forecast.demand_level
    )

    db.add(new_forecast)

    db.commit()

    db.refresh(new_forecast)

    return new_forecast


# ---------------------------------
# Get All Demand Forecasts
# ---------------------------------

def get_all_forecasts(
    db: Session
):

    return (
        db.query(DemandForecast)
        .all()
    )


# ---------------------------------
# Get Forecast By ID
# ---------------------------------

def get_forecast(
    db: Session,
    forecast_id: int
):

    return (
        db.query(DemandForecast)
        .filter(
            DemandForecast.id == forecast_id
        )
        .first()
    )


# ---------------------------------
# Delete Forecast
# ---------------------------------

def delete_forecast(
    db: Session,
    forecast_id: int
):

    forecast = (
        db.query(DemandForecast)
        .filter(
            DemandForecast.id == forecast_id
        )
        .first()
    )

    if forecast:

        db.delete(forecast)

        db.commit()

    return forecast