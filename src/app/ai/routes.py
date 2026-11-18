from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.ai.services import (
    generate_demand_recommendations,
    generate_fault_recommendations,
    evaluate_demand_forecast,
    evaluate_fault_detection,
)

from app.recommendations.schemas import RecommendationResponse


router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


@router.post(
    "/generate-demand-recommendations",
    response_model=list[RecommendationResponse]
)
def generate_demand(
    db: Session = Depends(get_db)
):
    return generate_demand_recommendations(db)


@router.post(
    "/generate-fault-recommendations",
    response_model=list[RecommendationResponse]
)
def generate_fault(
    db: Session = Depends(get_db)
):
    return generate_fault_recommendations(db)


@router.post("/evaluate-demand")
def evaluate_demand():
    actual_values = [50, 60, 70, 80]
    predicted_values = [52, 58, 72, 78]

    return evaluate_demand_forecast(
        actual_values,
        predicted_values
    )


@router.post("/evaluate-fault")
def evaluate_fault():

    actual_labels = [1, 0, 1, 1, 0, 1]
    predicted_labels = [1, 0, 1, 0, 0, 1]

    return evaluate_fault_detection(
        actual_labels,
        predicted_labels
    )