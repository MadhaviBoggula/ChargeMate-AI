
"""Scripted tool registry for evaluation (Member 4, lane E).

Implements the shared ToolRegistry protocol with the full owner and
driver tool schemas from the allocation document, so tool selection and
argument validity can be evaluated before Members 2/3 deploy their MCP
servers. Invocations are recorded for assertion; results are scripted
per tool and argument checks reject structurally invalid calls.
"""
import json
from typing import Any

OWNER_TOOLS = {
    "get_owner_stations": {
        "description": "List charging stations belonging to the owner.",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "limit": {"type": "integer"},
            },
        },
        "result": {
            "status": "ok",
            "data": {
                "stations": [
                    {"id": "st-1", "name": "Green Park Plaza", "status": "active"},
                    {"id": "st-2", "name": "Riverside Mall", "status": "active"},
                ]
            },
        },
    },
    "get_station_details": {
        "description": "Retrieve details of one owned station.",
        "parameters": {
            "type": "object",
            "properties": {"station_id": {"type": "string"}},
            "required": ["station_id"],
        },
        "result": {
            "status": "ok",
            "data": {"station": {"id": "st-1", "name": "Green Park Plaza"}},
        },
    },
    "get_charging_sessions": {
        "description": "Retrieve simulated charging sessions with filters.",
        "parameters": {
            "type": "object",
            "properties": {
                "station_id": {"type": "string"},
                "date_from": {"type": "string"},
                "date_to": {"type": "string"},
                "status": {"type": "string"},
            },
        },
        "result": {
            "status": "ok",
            "data": {"sessions": [{"id": "s-1", "energy_kwh": 42.5}]},
        },
    },
    "get_station_revenue": {
        "description": "Calculate revenue for a station and date range.",
        "parameters": {
            "type": "object",
            "properties": {
                "station_id": {"type": "string"},
                "date_from": {"type": "string"},
                "date_to": {"type": "string"},
            },
            "required": ["station_id"],
        },
        "result": {
            "status": "ok",
            "data": {"revenue": 1832.4, "currency": "USD"},
        },
    },
    "get_station_analytics": {
        "description": "Return operational analytics for the owner's network.",
        "parameters": {
            "type": "object",
            "properties": {"station_id": {"type": "string"}},
        },
        "result": {
            "status": "ok",
            "data": {
                "sessions": 128,
                "utilization": 0.61,
                "busiest_station": "Green Park Plaza",
            },
        },
    },
    "create_station": {
        "description": "Create a station under the owner.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "location": {"type": "string"},
            },
            "required": ["name", "location"],
        },
        "result": {
            "status": "ok",
            "data": {"station": {"id": "st-new", "name": "New Station"}},
        },
    },
    "update_station": {
        "description": "Update permitted fields on an owned station.",
        "parameters": {
            "type": "object",
            "properties": {
                "station_id": {"type": "string"},
                "fields": {"type": "object"},
            },
            "required": ["station_id", "fields"],
        },
        "result": {"status": "ok", "data": {"updated": True}},
    },
    "update_charger_status": {
        "description": "Change a charger status after ownership validation.",
        "parameters": {
            "type": "object",
            "properties": {
                "charger_id": {"type": "string"},
                "status": {"type": "string"},
            },
            "required": ["charger_id", "status"],
        },
        "result": {"status": "ok", "data": {"updated": True}},
    },
    "update_charging_price": {
        "description": "Update pricing for an owned charger or station.",
        "parameters": {
            "type": "object",
            "properties": {
                "station_id": {"type": "string"},
                "price_per_kwh": {"type": "number"},
            },
            "required": ["station_id", "price_per_kwh"],
        },
        "result": {"status": "ok", "data": {"updated": True}},
    },
}

DRIVER_TOOLS = {
    "search_stations": {
        "description": "Search stations using supported filters.",
        "parameters": {
            "type": "object",
            "properties": {
                "area": {"type": "string"},
                "connector": {"type": "string"},
                "min_power_kw": {"type": "number"},
                "max_price": {"type": "number"},
            },
        },
        "result": {
            "status": "ok",
            "data": {
                "stations": [
                    {"id": "st-1", "name": "Green Park Plaza", "connector": "CCS"}
                ]
            },
        },
    },
    "get_station_details": {
        "description": "Retrieve station information.",
        "parameters": {
            "type": "object",
            "properties": {"station_id": {"type": "string"}},
            "required": ["station_id"],
        },
        "result": {
            "status": "ok",
            "data": {"station": {"id": "st-1", "name": "Green Park Plaza"}},
        },
    },
    "check_station_availability": {
        "description": "Return database-derived simulated availability.",
        "parameters": {
            "type": "object",
            "properties": {
                "station_id": {"type": "string"},
                "start_at": {"type": "string"},
            },
            "required": ["station_id", "start_at"],
        },
        "result": {
            "status": "ok",
            "data": {"available": True, "open_slots": 3},
        },
    },
    "filter_compatible_stations": {
        "description": "Filter stations by vehicle connector compatibility.",
        "parameters": {
            "type": "object",
            "properties": {"vehicle_id": {"type": "string"}},
            "required": ["vehicle_id"],
        },
        "result": {
            "status": "ok",
            "data": {"stations": [{"id": "st-1", "name": "Green Park Plaza"}]},
        },
    },
    "get_driver_preferences": {
        "description": "Retrieve the driver's preferences.",
        "parameters": {"type": "object", "properties": {}},
        "result": {
            "status": "ok",
            "data": {"preferred_connector": "CCS", "max_price": 0.4},
        },
    },
    "update_driver_preferences": {
        "description": "Update permitted driver preferences.",
        "parameters": {
            "type": "object",
            "properties": {"fields": {"type": "object"}},
            "required": ["fields"],
        },
        "result": {"status": "ok", "data": {"updated": True}},
    },
    "get_favourite_stations": {
        "description": "Retrieve the driver's saved stations.",
        "parameters": {"type": "object", "properties": {}},
        "result": {"status": "ok", "data": {"stations": []}},
    },
    "add_favourite_station": {
        "description": "Save a station for the driver.",
        "parameters": {
            "type": "object",
            "properties": {"station_id": {"type": "string"}},
            "required": ["station_id"],
        },
        "result": {"status": "ok", "data": {"added": True}},
    },
    "remove_favourite_station": {
        "description": "Remove a saved station.",
        "parameters": {
            "type": "object",
            "properties": {"station_id": {"type": "string"}},
            "required": ["station_id"],
        },
        "result": {"status": "ok", "data": {"removed": True}},
    },
    "search_available_slots": {
        "description": "Find available charger slots by station/time/compatibility.",
        "parameters": {
            "type": "object",
            "properties": {
                "station_id": {"type": "string"},
                "start_at": {"type": "string"},
                "duration_minutes": {"type": "integer"},
            },
            "required": ["station_id", "start_at"],
        },
        "result": {
            "status": "ok",
            "data": {
                "slots": [
                    {"charger_id": "ch-1", "start_at": "2026-11-15T10:00:00Z"}
                ]
            },
        },
    },
    "prepare_booking": {
        "description": (
            "Prepare a booking proposal without reserving the slot. The "
            "proposal requires explicit user confirmation in the "
            "application before it can be executed."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "station_id": {"type": "string"},
                "charger_id": {"type": "string"},
                "start_at": {"type": "string"},
            },
            "required": ["station_id", "start_at"],
        },
        "result": {
            "status": "ok",
            "data": {
                "proposal_id": "prop-1",
                "station": "Green Park Plaza",
                "start_at": "2026-11-15T10:00:00Z",
                "duration_minutes": 30,
            },
        },
        "confirmation_request": {
            "tool": "confirm_booking",
            "arguments": {
                "proposal_id": "prop-1",
                "station_id": "st-1",
                "start_at": "2026-11-15T10:00:00Z",
            },
            "action": "book a 30-minute charging slot at Green Park Plaza",
            "summary": {
                "station": "Green Park Plaza",
                "start_at": "2026-11-15T10:00:00Z",
            },
        },
    },
    "confirm_booking": {
        "description": "Revalidate availability and create the booking.",
        "parameters": {
            "type": "object",
            "properties": {
                "proposal_id": {"type": "string"},
                "station_id": {"type": "string"},
                "start_at": {"type": "string"},
            },
            "required": ["proposal_id"],
        },
        "result": {
            "status": "ok",
            "data": {"booking_reference": "BK-2026-0001"},
        },
    },
    "get_my_bookings": {
        "description": "Retrieve the driver's booking records.",
        "parameters": {
            "type": "object",
            "properties": {"status": {"type": "string"}},
        },
        "result": {
            "status": "ok",
            "data": {"bookings": [{"reference": "BK-2026-0001"}]},
        },
    },
    "cancel_booking": {
        "description": "Cancel an eligible booking owned by the driver.",
        "parameters": {
            "type": "object",
            "properties": {"booking_reference": {"type": "string"}},
            "required": ["booking_reference"],
        },
        "result": {"status": "ok", "data": {"cancelled": True}},
    },
}


class ScriptedToolRegistry:
    """Deterministic ToolRegistry backed by the scripted tool tables."""

    def __init__(self, role: str):
        self.role = role.lower()
        self.tools = (
            OWNER_TOOLS if self.role == "owner" else DRIVER_TOOLS
        )
        self.invocations: list[dict[str, Any]] = []

    async def list_tools(self, role: str) -> list[dict[str, Any]]:
        schemas = []

        for name, spec in self.tools.items():
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": spec["description"],
                        "parameters": spec["parameters"],
                    },
                }
            )

        return schemas

    async def invoke_tool(
        self,
        role: str,
        name: str,
        arguments: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        self.invocations.append(
            {
                "tool": name,
                "arguments": arguments or {},
                "context": context or {},
            }
        )

        spec = self.tools.get(name)

        if spec is None:
            return {
                "status": "error",
                "detail": f"Unknown tool '{name}' for role '{self.role}'.",
            }

        self._validate_arguments(name, spec, arguments or {})

        result = dict(spec.get("result", {"status": "ok", "data": {}}))

        if spec.get("confirmation_request"):
            result["confirmation_request"] = spec["confirmation_request"]

        return result

    def _validate_arguments(
        self, name: str, spec: dict[str, Any], arguments: dict[str, Any]
    ) -> None:
        required = spec["parameters"].get("required", [])

        for key in required:
            if key not in arguments:
                raise ValueError(
                    f"Tool '{name}' is missing required argument '{key}'."
                )

    def tool_names_called(self) -> list[str]:
        return [invocation["tool"] for invocation in self.invocations]

    def calls_to_json(self) -> str:
        return json.dumps(self.invocations, default=str)
