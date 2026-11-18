from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.ai.services import (
    generate_demand_recommendations,
    generate_fault_recommendations,
)


router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


@router.post("/generate-demand-recommendations")
def generate_demand(
    db: Session = Depends(get_db)
):
    return generate_demand_recommendations(db)


@router.post("/generate-fault-recommendations")
def generate_fault(
    db: Session = Depends(get_db)
):
    return generate_fault_recommendations(db)