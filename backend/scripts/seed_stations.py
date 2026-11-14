
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import engine
from app.models.station import Station


SAMPLE_STATIONS = [
    {
        "name": "ChargeMate Central",
        "location": "Benz Circle",
        "address": "Benz Circle, Vijayawada, Andhra Pradesh",
        "connectors": ["CCS2", "Type 2"],
        "charger_type": "DC",
        "power": 60,
        "speed": "Fast",
        "available_slots": 5,
        "total_slots": 8,
        "price_per_kwh": 18,
        "description": (
            "A convenient charging destination with fast "
            "charging support and multiple connector options."
        ),
        "is_active": True,
    },
    {
        "name": "Green Energy Hub",
        "location": "MG Road",
        "address": "MG Road, Vijayawada, Andhra Pradesh",
        "connectors": ["Type 2"],
        "charger_type": "AC",
        "power": 22,
        "speed": "Standard",
        "available_slots": 3,
        "total_slots": 6,
        "price_per_kwh": 15,
        "description": (
            "An everyday charging option designed for "
            "convenient standard charging."
        ),
        "is_active": True,
    },
    {
        "name": "Urban Charge Point",
        "location": "Auto Nagar",
        "address": "Auto Nagar, Vijayawada, Andhra Pradesh",
        "connectors": ["CCS2", "CHAdeMO"],
        "charger_type": "DC",
        "power": 90,
        "speed": "Fast",
        "available_slots": 2,
        "total_slots": 5,
        "price_per_kwh": 20,
        "description": (
            "A high-power charging option with DC charging support."
        ),
        "is_active": True,
    },
    {
        "name": "EcoDrive Station",
        "location": "Poranki",
        "address": "Poranki, Vijayawada, Andhra Pradesh",
        "connectors": ["Type 2", "CCS2"],
        "charger_type": "AC",
        "power": 30,
        "speed": "Standard",
        "available_slots": 4,
        "total_slots": 7,
        "price_per_kwh": 16,
        "description": (
            "A practical charging option with multiple "
            "connector standards."
        ),
        "is_active": True,
    },
]


def seed_stations():
    inserted = 0
    skipped = 0

    with Session(engine) as db:
        for station_data in SAMPLE_STATIONS:
            existing = db.scalar(
                select(Station).where(
                    Station.name == station_data["name"]
                )
            )

            if existing:
                print(f"Already exists: {station_data['name']}")
                skipped += 1
                continue

            db.add(Station(**station_data))
            inserted += 1

        db.commit()

    print("\nStation seeding completed.")
    print(f"Inserted: {inserted}")
    print(f"Skipped: {skipped}")


if __name__ == "__main__":
    seed_stations()
