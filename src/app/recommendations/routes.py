from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.auth.dependencies import get_current_admin

from app.recommendations.schemas import (
    RecommendationCreate,
    RecommendationResponse,
)

from app.recommendations.repository import (
    create_recommendation,
    get_all_recommendations,
    get_recommendation,
    delete_recommendation,
)


router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)


# Create Recommendation
@router.post(
    "/",
    response_model=RecommendationResponse
)
def create(
    recommendation: RecommendationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    return create_recommendation(
        db,
        recommendation
    )


# Get All Recommendations
@router.get(
    "/",
    response_model=list[RecommendationResponse]
)
def get_all(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    return get_all_recommendations(db)


# Get Single Recommendation
@router.get(
    "/{recommendation_id}",
    response_model=RecommendationResponse
)
def get_one(
    recommendation_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    return get_recommendation(
        db,
        recommendation_id
    )


# Delete Recommendation
@router.delete(
    "/{recommendation_id}"
)
def delete(
    recommendation_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):

    delete_recommendation(
        db,
        recommendation_id
    )

    return {
        "message": "Recommendation deleted successfully"
    }