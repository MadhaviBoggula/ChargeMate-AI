from sqlalchemy.orm import Session

from app.simulation.models import Scenario
from app.simulation.schemas import ScenarioCreate, ScenarioUpdate


def create_scenario(
    db: Session,
    scenario: ScenarioCreate
):
    new_scenario = Scenario(
        name=scenario.name,
        description=scenario.description,
        initial_state=scenario.initial_state,
        current_state=scenario.current_state
    )

    db.add(new_scenario)
    db.commit()
    db.refresh(new_scenario)

    return new_scenario


def get_all_scenarios(db: Session):

    return db.query(Scenario).all()


def get_scenario(
    db: Session,
    scenario_id: int
):

    return (
        db.query(Scenario)
        .filter(Scenario.id == scenario_id)
        .first()
    )


def update_scenario(
    db: Session,
    scenario_id: int,
    scenario: ScenarioUpdate
):

    existing = get_scenario(db, scenario_id)

    if not existing:
        return None

    if scenario.name is not None:
        existing.name = scenario.name

    if scenario.description is not None:
        existing.description = scenario.description

    if scenario.current_state is not None:
        existing.current_state = scenario.current_state

    db.commit()
    db.refresh(existing)

    return existing


def delete_scenario(
    db: Session,
    scenario_id: int
):

    existing = get_scenario(db, scenario_id)

    if not existing:
        return None

    db.delete(existing)
    db.commit()

    return existing