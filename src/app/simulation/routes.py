from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.auth.dependencies import get_current_admin

from app.simulation.schemas import (
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioResponse,
)

from app.simulation.repository import (
    create_scenario,
    get_all_scenarios,
    get_scenario,
    update_scenario,
    delete_scenario,
)


router = APIRouter(
    prefix="/simulation",
    tags=["Simulation"]
)


# Create Scenario
@router.post(
    "/",
    response_model=ScenarioResponse
)
def create(
    scenario: ScenarioCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    return create_scenario(db, scenario)


# Get All Scenarios
@router.get(
    "/",
    response_model=list[ScenarioResponse]
)
def get_all(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    return get_all_scenarios(db)


# Get Single Scenario
@router.get(
    "/{scenario_id}",
    response_model=ScenarioResponse
)
def get_one(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    return get_scenario(db, scenario_id)


# Update Scenario
@router.put(
    "/{scenario_id}",
    response_model=ScenarioResponse
)
def update(
    scenario_id: int,
    scenario: ScenarioUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    return update_scenario(
        db,
        scenario_id,
        scenario
    )


# Delete Scenario
@router.delete(
    "/{scenario_id}"
)
def delete(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    delete_scenario(
        db,
        scenario_id
    )

    return {
        "message": "Scenario deleted successfully"
    }