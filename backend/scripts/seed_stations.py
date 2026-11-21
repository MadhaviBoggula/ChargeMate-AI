"""Seed ChargeMate with demo owners, drivers, stations, and sessions.

The script is idempotent: existing users and stations are reused, and
sessions are only generated for stations that do not have any yet.

Run from the backend directory:

    python -m scripts.seed_stations
"""

import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.session import SessionLocal
from app.models.charger import Charger
from app.models.charging_session import ChargingSession
from app.models.connector import Connector
from app.models.driver_preference import DriverPreference
from app.models.favourite_station import FavouriteStation
from app.models.station import ChargingStation
from app.models.user import User, UserRole
from app.models.vehicle import Vehicle
from app.services.password import hash_password


OWNER_EMAIL = "owner@chargemate.test"
OWNER_PASSWORD = "OwnerPass123!"
DRIVER_EMAIL = "driver@chargemate.test"
DRIVER_PASSWORD = "DriverPass123!"


STATIONS = [
    {
        "name": "ChargeMate Central",
        "description": "Fast DC charging near Benz Circle.",
        "address_line1": "Benz Circle",
        "address_line2": "MG Road",
        "city": "Vijayawada",
        "state": "Andhra Pradesh",
        "pincode": "520010",
        "latitude": 16.5062,
        "longitude": 80.6480,
        "chargers": [
            {
                "charger_code": "CMC-DC-01",
                "charging_type": "DC",
                "power_kw": Decimal("60.00"),
                "price_per_kwh": Decimal("18.50"),
                "connectors": [
                    ("CCS2", Decimal("60.00")),
                    ("CHAdeMO", Decimal("50.00")),
                ],
            },
            {
                "charger_code": "CMC-AC-01",
                "charging_type": "AC",
                "power_kw": Decimal("22.00"),
                "price_per_kwh": Decimal("12.00"),
                "connectors": [("Type 2", Decimal("22.00"))],
            },
        ],
    },
    {
        "name": "Green Energy Hub",
        "description": "Everyday AC charging on MG Road.",
        "address_line1": "MG Road",
        "city": "Vijayawada",
        "state": "Andhra Pradesh",
        "pincode": "520010",
        "latitude": 16.5100,
        "longitude": 80.6400,
        "chargers": [
            {
                "charger_code": "GEH-AC-01",
                "charging_type": "AC",
                "power_kw": Decimal("22.00"),
                "price_per_kwh": Decimal("11.00"),
                "connectors": [("Type 2", Decimal("22.00"))],
            },
            {
                "charger_code": "GEH-AC-02",
                "charging_type": "AC",
                "power_kw": Decimal("7.40"),
                "price_per_kwh": Decimal("8.00"),
                "connectors": [("Type 2", Decimal("7.40"))],
            },
        ],
    },
    {
        "name": "Urban Charge Point",
        "description": "High-power charging in Auto Nagar.",
        "address_line1": "Auto Nagar",
        "city": "Vijayawada",
        "state": "Andhra Pradesh",
        "pincode": "520007",
        "latitude": 16.4930,
        "longitude": 80.6700,
        "chargers": [
            {
                "charger_code": "UCP-DC-01",
                "charging_type": "DC",
                "power_kw": Decimal("90.00"),
                "price_per_kwh": Decimal("20.00"),
                "connectors": [("CCS2", Decimal("90.00"))],
            },
            {
                "charger_code": "UCP-DC-02",
                "charging_type": "DC",
                "power_kw": Decimal("50.00"),
                "price_per_kwh": Decimal("17.00"),
                "connectors": [
                    ("CCS2", Decimal("50.00")),
                    ("CHAdeMO", Decimal("50.00")),
                ],
            },
        ],
    },
]


def get_or_create_user(
    db: Session,
    *,
    name: str,
    email: str,
    password: str,
    role: UserRole,
) -> User:
    user = db.scalar(select(User).where(User.email == email))

    if user is not None:
        return user

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.flush()
    return user


def seed_sessions(
    db: Session,
    station: ChargingStation,
    driver: User,
) -> int:
    existing = db.scalar(
        select(ChargingSession.id).where(
            ChargingSession.station_id == station.id
        )
    )

    if existing is not None:
        return 0

    now = datetime.now(timezone.utc)
    created = 0

    for index, charger in enumerate(station.chargers):
        for offset in range(3):
            started_at = now - timedelta(
                days=2 + offset + index,
                hours=3 + offset,
            )
            duration = 30 + (offset * 15)
            energy = (
                charger.power_kw * Decimal(duration) / Decimal("60")
            ).quantize(Decimal("0.001"))
            revenue = (energy * charger.price_per_kwh).quantize(
                Decimal("0.01")
            )

            db.add(
                ChargingSession(
                    station_id=station.id,
                    charger_id=charger.id,
                    driver_id=driver.id,
                    started_at=started_at,
                    ended_at=started_at + timedelta(minutes=duration),
                    energy_kwh=energy,
                    duration_minutes=duration,
                    price_per_kwh=charger.price_per_kwh,
                    revenue=revenue,
                    status="completed",
                )
            )
            created += 1

    return created


def seed_driver_profile(
    db: Session,
    driver: User,
    stations: list[ChargingStation],
) -> None:
    """Give the demo driver a vehicle, preferences, and favourites."""

    vehicle = db.scalar(
        select(Vehicle).where(
            Vehicle.driver_id == driver.id,
            Vehicle.registration_number == "AP16 CM 2024",
        )
    )

    if vehicle is None:
        vehicle = Vehicle(
            driver_id=driver.id,
            registration_number="AP16 CM 2024",
            nickname="Demo EV",
            vehicle_model="Tata Nexon EV",
            vehicle_type="car",
            manufacturing_year=2024,
            battery_capacity_kwh=Decimal("40.50"),
            connector_type="CCS2",
            is_primary=True,
        )
        db.add(vehicle)
        db.flush()

    preference = db.scalar(
        select(DriverPreference).where(
            DriverPreference.driver_id == driver.id
        )
    )

    if preference is None:
        db.add(
            DriverPreference(
                driver_id=driver.id,
                preferred_connector_type="CCS2",
                preferred_charging_type="DC",
                max_price_per_kwh=Decimal("25.00"),
                preferred_city="Vijayawada",
                default_vehicle_id=vehicle.id,
            )
        )

    for station in stations[:2]:
        favourite = db.scalar(
            select(FavouriteStation).where(
                FavouriteStation.driver_id == driver.id,
                FavouriteStation.station_id == station.id,
            )
        )

        if favourite is None:
            db.add(
                FavouriteStation(
                    driver_id=driver.id,
                    station_id=station.id,
                )
            )


def seed() -> None:
    with SessionLocal() as db:
        owner = get_or_create_user(
            db,
            name="Demo Owner",
            email=OWNER_EMAIL,
            password=OWNER_PASSWORD,
            role=UserRole.OWNER,
        )
        driver = get_or_create_user(
            db,
            name="Demo Driver",
            email=DRIVER_EMAIL,
            password=DRIVER_PASSWORD,
            role=UserRole.DRIVER,
        )

        inserted_stations = 0
        inserted_chargers = 0
        inserted_sessions = 0
        seeded_stations: list[ChargingStation] = []

        for station_data in STATIONS:
            station = db.scalar(
                select(ChargingStation).where(
                    ChargingStation.owner_id == owner.id,
                    ChargingStation.name == station_data["name"],
                )
            )

            if station is None:
                data = dict(station_data)
                chargers = data.pop("chargers")
                station = ChargingStation(
                    owner_id=owner.id,
                    **data,
                )
                for charger_data in chargers:
                    charger_values = dict(charger_data)
                    connectors = charger_values.pop("connectors")
                    charger = Charger(**charger_values)
                    charger.connectors = [
                        Connector(
                            connector_type=connector_type,
                            power_kw=power_kw,
                        )
                        for connector_type, power_kw in connectors
                    ]
                    station.chargers.append(charger)
                db.add(station)
                db.flush()
                inserted_stations += 1
                inserted_chargers += len(station.chargers)

            db.refresh(station)
            seeded_stations.append(station)
            inserted_sessions += seed_sessions(db, station, driver)

        seed_driver_profile(db, driver, seeded_stations)

        db.commit()

    print("Seed complete.")
    print(f"Owner:    {OWNER_EMAIL} / {OWNER_PASSWORD}")
    print(f"Driver:   {DRIVER_EMAIL} / {DRIVER_PASSWORD}")
    print(f"Stations inserted: {inserted_stations}")
    print(f"Chargers inserted: {inserted_chargers}")
    print(f"Sessions inserted: {inserted_sessions}")


if __name__ == "__main__":
    seed()
