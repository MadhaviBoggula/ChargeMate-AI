"""PostgreSQL-only booking concurrency tests.

Run against a real PostgreSQL database (pgvector image is convenient):

    TEST_DATABASE_URL=postgresql+psycopg://user:pass@host:5432/db \
        pytest tests/test_booking_concurrency_pg.py

Each test module creates and drops its own schema, so the database is
never modified outside that schema.
"""
import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - register all models on Base.metadata
from app.core.errors import ConflictError
from app.database.base import Base
from app.models.booking import ChargingBooking
from app.models.charger import Charger
from app.models.connector import Connector
from app.models.pending_confirmation import PendingConfirmation
from app.models.station import ChargingStation
from app.models.user import User, UserRole
from app.services import booking_service
from app.services.password import hash_password
from app.services.time_utils import align_up

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL is not configured",
)


@pytest.fixture(scope="module")
def pg_factory():
    schema = f"test_booking_{uuid.uuid4().hex[:10]}"

    admin_engine = create_engine(TEST_DATABASE_URL, isolation_level="AUTOCOMMIT")

    with admin_engine.connect() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))

    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"options": f"-csearch_path={schema},public"},
    )

    Base.metadata.create_all(engine, checkfirst=False)

    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
        connection.execute(
            text(
                f"""
                ALTER TABLE "{schema}".charging_bookings
                ADD CONSTRAINT ex_charging_bookings_no_overlap
                EXCLUDE USING gist (
                    charger_id WITH =,
                    tstzrange(start_at, end_at) WITH &&
                )
                WHERE (status = 'CONFIRMED')
                """
            )
        )

    factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    try:
        yield factory
    finally:
        engine.dispose()

        with admin_engine.connect() as connection:
            connection.execute(
                text(f'DROP SCHEMA "{schema}" CASCADE')
            )

        admin_engine.dispose()


def make_user(db, email, role):
    user = User(
        name=email.split("@")[0],
        email=email,
        password_hash=hash_password("TestPassword123!"),
        role=role,
    )
    db.add(user)
    db.flush()
    return user


def seed_booking_world(factory, slot_start):
    suffix = uuid.uuid4().hex[:8]

    with factory() as db:
        owner = make_user(
            db,
            f"pg-owner-{suffix}@example.com",
            UserRole.OWNER,
        )
        driver_one = make_user(
            db,
            f"pg-driver-one-{suffix}@example.com",
            UserRole.DRIVER,
        )
        driver_two = make_user(
            db,
            f"pg-driver-two-{suffix}@example.com",
            UserRole.DRIVER,
        )

        station = ChargingStation(
            owner_id=owner.id,
            name="PG Concurrency Station",
            city="Vijayawada",
            state="Andhra Pradesh",
            pincode="520010",
            timezone="Asia/Kolkata",
        )
        charger = Charger(
            charger_code=f"PG-DC-{uuid.uuid4().hex[:6]}",
            charging_type="DC",
            power_kw=Decimal("60.00"),
            price_per_kwh=Decimal("18.00"),
        )
        charger.connectors.append(
            Connector(
                connector_type="CCS2",
                power_kw=Decimal("60.00"),
            )
        )
        station.chargers.append(charger)
        db.add(station)
        db.flush()

        slot_end = slot_start + timedelta(minutes=30)
        proposals = []

        for driver in (driver_one, driver_two):
            proposal = PendingConfirmation(
                user_id=driver.id,
                action="confirm_booking",
                tool="confirm_booking",
                arguments={
                    "station_id": str(station.id),
                    "charger_id": str(charger.id),
                    "vehicle_id": None,
                    "connector_type": "CCS2",
                    "start_at": slot_start.isoformat(),
                    "end_at": slot_end.isoformat(),
                    "duration_minutes": 30,
                    "estimated_price": "540.00",
                },
                summary={"station_name": station.name},
                status="pending",
                expires_at=datetime.now(timezone.utc)
                + timedelta(minutes=10),
            )
            db.add(proposal)
            db.flush()
            proposals.append((driver.id, proposal.id))

        db.commit()

        return {
            "station_id": station.id,
            "charger_id": charger.id,
            "proposals": proposals,
        }


def test_database_rejects_overlapping_confirmed_bookings(pg_factory):
    slot_start = align_up(
        datetime.now(timezone.utc) + timedelta(days=1),
        30,
        "Asia/Kolkata",
    )
    world = seed_booking_world(pg_factory, slot_start)

    with pg_factory() as db:
        db.add(
            ChargingBooking(
                booking_reference=f"CM-{uuid.uuid4().hex[:6].upper()}",
                driver_id=world["proposals"][0][0],
                station_id=world["station_id"],
                charger_id=world["charger_id"],
                connector_type="CCS2",
                start_at=slot_start,
                end_at=slot_start + timedelta(minutes=30),
                status="CONFIRMED",
            )
        )
        db.commit()

    with pg_factory() as db:
        db.add(
            ChargingBooking(
                booking_reference=f"CM-{uuid.uuid4().hex[:6].upper()}",
                driver_id=world["proposals"][1][0],
                station_id=world["station_id"],
                charger_id=world["charger_id"],
                connector_type="CCS2",
                start_at=slot_start + timedelta(minutes=15),
                end_at=slot_start + timedelta(minutes=45),
                status="CONFIRMED",
            )
        )

        with pytest.raises(IntegrityError):
            db.commit()


def test_concurrent_confirms_produce_one_success_one_conflict(pg_factory):
    slot_start = align_up(
        datetime.now(timezone.utc) + timedelta(days=2),
        30,
        "Asia/Kolkata",
    )
    world = seed_booking_world(pg_factory, slot_start)

    barrier = threading.Barrier(2)

    def confirm(driver_id, proposal_id):
        session = pg_factory()

        try:
            barrier.wait(timeout=10)

            try:
                booking = booking_service.confirm_booking(
                    session,
                    driver_id,
                    proposal_id,
                )
                return {"status": "confirmed", "reference": booking.booking_reference}
            except ConflictError:
                return {"status": "conflict"}
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(confirm, driver_id, proposal_id)
            for driver_id, proposal_id in world["proposals"]
        ]
        results = [future.result(timeout=30) for future in futures]

    statuses = sorted(result["status"] for result in results)

    assert statuses == ["confirmed", "conflict"], results

    with pg_factory() as db:
        count = db.scalar(
            select(func.count(ChargingBooking.id)).where(
                ChargingBooking.charger_id == world["charger_id"],
                ChargingBooking.status == "CONFIRMED",
            )
        )

    assert count == 1
