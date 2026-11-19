from sqlalchemy.orm import Session

from app.ai.models import DemandForecast, FaultDetection
from app.recommendations.models import Recommendation


def generate_demand_recommendations(
    db: Session
):
    forecasts = (
        db.query(DemandForecast)
        .filter(
            DemandForecast.demand_level.ilike("high")
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
            FaultDetection.severity.ilike("high")
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

import math

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    recall_score,
    f1_score
)


def evaluate_demand_forecast(
    actual_values,
    predicted_values
):
    mae = mean_absolute_error(
        actual_values,
        predicted_values
    )

    rmse = math.sqrt(
        mean_squared_error(
            actual_values,
            predicted_values
        )
    )

    return {
        "mae": round(mae, 3),
        "rmse": round(rmse, 3)
    }


def evaluate_fault_detection(
    actual_labels,
    predicted_labels
):

    precision = precision_score(
        actual_labels,
        predicted_labels,
        zero_division=0
    )

    recall = recall_score(
        actual_labels,
        predicted_labels,
        zero_division=0
    )

    f1 = f1_score(
        actual_labels,
        predicted_labels,
        zero_division=0
    )

    false_positives = sum(
        1
        for actual, predicted in zip(
            actual_labels,
            predicted_labels
        )
        if actual == 0 and predicted == 1
    )

    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1_score": round(f1, 3),
        "false_positives": false_positives
    }