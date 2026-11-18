from sqlalchemy.orm import Session

from app.recommendations.models import Recommendation
from app.recommendations.schemas import RecommendationCreate


def create_recommendation(
    db: Session,
    recommendation: RecommendationCreate
):
    db_recommendation = Recommendation(
        station_id=recommendation.station_id,
        recommendation_type=recommendation.recommendation_type,
        message=recommendation.message,
        priority=recommendation.priority,
        confidence=recommendation.confidence
    )

    db.add(db_recommendation)
    db.commit()
    db.refresh(db_recommendation)

    return db_recommendation


def get_all_recommendations(
    db: Session
):
    return db.query(Recommendation).all()


def get_recommendation(
    db: Session,
    recommendation_id: int
):
    return (
        db.query(Recommendation)
        .filter(
            Recommendation.id == recommendation_id
        )
        .first()
    )


def delete_recommendation(
    db: Session,
    recommendation_id: int
):
    recommendation = get_recommendation(
        db,
        recommendation_id
    )

    if recommendation:
        db.delete(recommendation)
        db.commit()

    return recommendation