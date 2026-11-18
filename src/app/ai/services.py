from sqlalchemy.orm import Session

from app.ai.models import DemandForecast, FaultDetection
from app.recommendations.models import Recommendation


def generate_demand_recommendations(
    db: Session
):
    forecasts = (
        db.query(DemandForecast)
        .filter(
            DemandForecast.demand_level == "high"
        )
        .all()
    )

    recommendations = []

    for forecast in forecasts:

        recommendation = Recommendation(
            station_id=forecast.station_id,
            recommendation_type="demand_management",
            message="High demand expected. Enable load balancing.",
            priority="high",
            confidence=0.90
        )

        db.add(recommendation)
        recommendations.append(recommendation)

    db.commit()

    return recommendations



def generate_fault_recommendations(
    db: Session
):
    faults = (
        db.query(FaultDetection)
        .filter(
            FaultDetection.severity == "high"
        )
        .all()
    )

    recommendations = []

    for fault in faults:

        recommendation = Recommendation(
            station_id=fault.station_id,
            recommendation_type="fault_alert",
            message="High severity fault detected. Schedule maintenance.",
            priority="high",
            confidence=fault.confidence
        )

        db.add(recommendation)
        recommendations.append(recommendation)

    db.commit()

    return recommendations