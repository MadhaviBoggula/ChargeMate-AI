from mcp.server.fastmcp import FastMCP
from app.config import settings
from app.database import SessionLocal
from app.services.owner_service import list_stations, get_station, list_chargers, set_charger_status

mcp = FastMCP("chargemate-owner-tools")

@mcp.tool()
def list_my_stations() -> list[dict]:
    """List charging stations belonging to the configured owner."""
    with SessionLocal() as db:
        return [
            {"id": s.id, "name": s.name, "address_id": s.address_id, "description": s.description}
            for s in list_stations(db, settings.mcp_owner_id)
        ]

@mcp.tool()
def get_station_details(station_id: int) -> dict:
    """Get details for one station owned by the configured owner."""
    with SessionLocal() as db:
        s = get_station(db, settings.mcp_owner_id, station_id)
        if not s:
            return {"error": "Station not found"}
        return {
            "id": s.id, "name": s.name, "owner_id": s.owner_id,
            "address_id": s.address_id, "description": s.description,
            "chargers": [
                {"id": c.id, "charger_code": c.charger_code, "status": c.status,
                 "availability": c.availability, "power_kw": str(c.power_kw)}
                for c in s.chargers
            ],
        }

@mcp.tool()
def list_my_chargers() -> list[dict]:
    """List chargers across stations belonging to the configured owner."""
    with SessionLocal() as db:
        return [
            {"id": c.id, "station_id": c.station_id, "charger_code": c.charger_code,
             "status": c.status, "availability": c.availability,
             "charging_type": c.charging_type, "power_kw": str(c.power_kw),
             "price_per_kwh": str(c.price_per_kwh)}
            for c in list_chargers(db, settings.mcp_owner_id)
        ]

@mcp.tool()
def update_charger_status(charger_id: int, status: str) -> dict:
    """Update status of a charger owned by the configured owner."""
    with SessionLocal() as db:
        c = set_charger_status(db, settings.mcp_owner_id, charger_id, status)
        if not c:
            return {"error": "Charger not found"}
        return {"id": c.id, "charger_code": c.charger_code, "status": c.status}

if __name__ == "__main__":
    mcp.run(transport="stdio")
