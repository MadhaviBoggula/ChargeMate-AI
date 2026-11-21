# ChargeMate AI Backend

FastAPI backend for an AI-powered EV charging platform with two roles:
station owners manage their network, drivers discover stations and book
simulated 30-minute charging slots. Conversations run through role-specific
LangGraph workflows that select between RAG knowledge, MCP tools, and general
answers. Sensitive operations require an explicit server-side confirmation.

## Stack

- Python 3.11+, FastAPI, Pydantic v2
- SQLAlchemy 2 and Alembic
- PostgreSQL with pgvector (Neon or local)
- JWT authentication and role/ownership authorization
- LangGraph workflows, OpenRouter LLM (OpenAI-compatible)
- MCP Python SDK (stdio locally, streamable HTTP in Docker)
- Local sentence-transformers embeddings (no embedding API key required)

## Project structure

```text
backend/
├── app/
│   ├── api/
│   │   ├── deps.py                 # JWT identity + role guards
│   │   └── routes/                 # auth, conversations, chat, owner, driver, bookings, stations
│   ├── agents/
│   │   ├── shared/                 # graph state, runtime, nodes, tool registry, memory
│   │   ├── owner/graph.py
│   │   └── driver/graph.py
│   ├── core/                       # settings, error types
│   ├── database/                   # Base, session, mixins
│   ├── mcp/
│   │   ├── client.py               # MCP tool registry (auth_context injection)
│   │   ├── owner_server.py         # 9 owner tools
│   │   ├── driver_server.py        # 15 driver tools
│   │   ├── auth.py                 # trusted identity validation
│   │   └── serializers.py
│   ├── models/                     # users, stations, chargers, connectors, sessions,
│   │                               # vehicles, preferences, favourites, bookings,
│   │                               # pending confirmations, conversations
│   ├── rag/                        # ingestion, embeddings, pgvector retrieval
│   ├── schemas/
│   ├── services/                   # owner, station, driver, booking, confirmation
│   ├── llm/                        # OpenRouter client and role prompts
│   └── main.py
├── knowledge_base/{owner,driver}/  # role-scoped seed documents
├── migrations/versions/            # single clean chain to 0005
├── scripts/                        # seed_stations.py, ingest_docs.py, evaluate_ai.py
└── tests/
```

## Setup

```bash
cd backend
uv sync
cp .env.example .env      # then fill DATABASE_URL, JWT_SECRET_KEY, OPENROUTER_*
```

A plain virtualenv works too:

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install fastapi "uvicorn[standard]" pydantic-settings \
  sqlalchemy "psycopg[binary]" alembic PyJWT "pwdlib[argon2]" email-validator \
  langgraph==0.2.60 "mcp>=1.9,<2" langchain-core==0.3.29 langchain-huggingface==0.1.2 \
  langchain-text-splitters==0.3.4 pgvector==0.3.6 pypdf python-docx openai groq anthropic \
  pytest pytest-asyncio httpx
```

`DATABASE_URL` must point at PostgreSQL with the `vector` extension available.
The first migration enables `vector`; booking overlap protection enables
`btree_gist`.

## Database

```bash
alembic upgrade head        # apply the full chain
alembic check               # confirm models and migrations agree
alembic current             # show the current head
```

Migration chain: `6ceff4e7f9ea -> 0002_rag_knowledge -> 0003_owner_domain ->
0004_driver_domain -> 0005_bookings`.

## Seed data

```bash
python scripts/seed_stations.py     # owners, drivers, stations, chargers, sessions,
                                    # demo vehicle, preferences, favourites
python scripts/ingest_docs.py       # index knowledge_base/{owner,driver}
python scripts/ingest_docs.py --reindex
```

Demo owner: `owner@chargemate.test / OwnerPass123!`
Demo driver: `driver@chargemate.test / DriverPass123!`

## Run the API

```bash
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- OpenAPI: http://127.0.0.1:8000/docs
- Health: `/health`, readiness (DB check): `/ready`

## API surface

All routes are under `/api/v1`. Every route below except registration, login,
and public discovery requires `Authorization: Bearer <token>`.

### Authentication
| Method | Path |
|---|---|
| POST | `/auth/register` (role: `owner` or `driver`) |
| POST | `/auth/login` |
| GET | `/auth/me` |

### Conversations and chat
| Method | Path | Notes |
|---|---|---|
| POST | `/chat` | The only writer of messages. `confirmation_action` is `confirm` or `reject`. |
| POST/GET | `/conversations` | Own conversations only. |
| GET | `/conversations/{id}` | Includes messages and confirmation metadata. |

There is no public message-creation endpoint, so clients cannot forge
assistant, system, or tool messages.

### Public discovery
| Method | Path |
|---|---|
| GET | `/stations` (city, connector, AC/DC, power, price, availability) |
| GET | `/stations/{id}` |
| GET | `/stations/{id}/availability` |
| GET | `/stations/{id}/available-slots` |

`available-slots` accepts `date` (station-local `YYYY-MM-DD`), or `start_at` /
`end_at` ISO timestamps, plus `duration_minutes`, `connector_type`,
`charging_type`, `max_price_per_kwh`, and `limit`.

### Owner
| Method | Path |
|---|---|
| POST/GET | `/owner/stations` |
| GET/PATCH/DELETE | `/owner/stations/{id}` (delete = soft deactivate) |
| POST | `/owner/stations/{id}/chargers` |
| GET | `/owner/chargers`, `/owner/chargers/{id}` |
| PATCH | `/owner/chargers/{id}`, `/owner/chargers/{id}/status`, `/owner/chargers/{id}/price` |
| GET | `/owner/sessions` (station, charger, period, status) |
| GET | `/owner/revenue`, `/owner/stations/{id}/revenue` |
| GET | `/owner/analytics`, `/owner/stations/{id}/analytics` |

### Driver
| Method | Path |
|---|---|
| POST/GET | `/driver/vehicles` |
| GET/PATCH/DELETE | `/driver/vehicles/{id}` |
| GET/PUT | `/driver/preferences` |
| GET | `/driver/favourites` |
| POST/DELETE | `/driver/favourites/{station_id}` |
| GET | `/driver/compatible-stations` |

### Bookings
| Method | Path |
|---|---|
| POST | `/bookings/proposals` (creates a reviewable summary, reserves nothing) |
| POST | `/bookings/{confirmation_id}/confirm` |
| GET | `/bookings` (status, station, upcoming_only) |
| GET | `/bookings/{booking_reference}` |
| POST | `/bookings/{booking_reference}/cancel` |

## Booking and confirmation rules

- Slots are fixed 30-minute intervals; storage is UTC, display follows the
  station timezone (default `Asia/Kolkata`).
- Only active stations and chargers with an active matching connector can be
  booked. A vehicle's connector is validated when a vehicle is supplied.
- A proposal creates a `pending_confirmations` row and does not block the slot.
- Confirmation rechecks availability in a transaction with a charger row lock;
  PostgreSQL also enforces an exclusion constraint over confirmed intervals.
- A confirmed booking gets a unique `CM-YYYYMMDD-XXXXXX` reference.
- Drivers see and cancel only their own bookings. Cancellation closes 30
  minutes before the start time; cancelled bookings remain for history.
- Confirmation state is server-side. LLM text can never approve an operation;
  only an explicit `confirmation_action` from the API or an approved MCP call
  can execute a pending action.

## MCP servers

The backend's `MCPToolRegistry` injects a trusted `auth_context`
(`user_id`, `role`, `conversation_id`, `approved`) into every tool call and
removes the argument from the schema shown to the LLM. Tools verify the user
still exists, is active, and has the server's role.

Owner server (9 tools):
`get_owner_stations`, `get_station_details`, `get_charging_sessions`,
`get_station_revenue`, `get_station_analytics`, `create_station`,
`update_station`, `update_charger_status`, `update_charging_price`.

Driver server (15 tools):
`search_stations`, `get_station_details`, `check_station_availability`,
`filter_compatible_stations`, `get_driver_preferences`,
`update_driver_preferences`, `get_favourite_stations`, `add_favourite_station`,
`remove_favourite_station`, `search_available_slots`, `prepare_booking`,
`confirm_booking`, `get_my_bookings`, `get_booking_details`, `cancel_booking`.

Run locally over stdio:

```bash
python -m app.mcp.owner_server
python -m app.mcp.driver_server
```

and point the backend at them:

```env
MCP_OWNER_SERVER_URL=.venv/Scripts/python.exe -m app.mcp.owner_server
MCP_DRIVER_SERVER_URL=.venv/Scripts/python.exe -m app.mcp.driver_server
```

Run over streamable HTTP:

```bash
MCP_TRANSPORT=streamable-http MCP_HOST=0.0.0.0 MCP_PORT=8101 python -m app.mcp.owner_server
MCP_TRANSPORT=streamable-http MCP_HOST=0.0.0.0 MCP_PORT=8102 python -m app.mcp.driver_server
```

## Tests

```bash
pytest -v
```

The default suite uses an isolated in-memory SQLite database for API, service,
agent, and MCP-tool tests. PostgreSQL-only tests are skipped unless
`TEST_DATABASE_URL` is set:

```bash
TEST_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/chargemate \
  pytest tests/test_booking_concurrency_pg.py -v
```

Those tests create a temporary schema, enable `btree_gist`, install the
exclusion constraint, and verify that concurrent confirmations produce exactly
one booking and one conflict. RAG tests run against `DATABASE_URL` and index
the seed documents.

## Docker

From the repository root:

```bash
docker compose up --build
```

Compose starts:

- `db` — pgvector PostgreSQL
- `migrate` — runs `alembic upgrade head` once
- `owner-mcp` and `driver-mcp` — streamable HTTP MCP servers on 8101/8102
- `backend` — FastAPI on http://127.0.0.1:8000

The backend receives `MCP_OWNER_SERVER_URL` and `MCP_DRIVER_SERVER_URL` for the
internal MCP services. Compose overrides `DATABASE_URL` with the local `db`
service; point it at Neon to run the stack against a hosted database.

## Security notes

- JWT access tokens carry `sub`, `role`, `iat`, and `exp`; the role claim must
  match the current database role.
- Role guards and ownership scoping are enforced in dependencies and services,
  never by the client or the LLM.
- Owner tools are unavailable to drivers and vice versa.
- Sensitive MCP operations return a confirmation request unless the backend
  marks the call approved from an explicit user action.
- Every response carries `X-Request-ID`, and errors use a consistent envelope
  with `detail`, `error`, and `request_id`.
