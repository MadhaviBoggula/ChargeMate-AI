# ChargeMate AI

AI-powered EV charging assistant with two role-specific experiences:

- **Station owners** retrieve stations, chargers, sessions, revenue, and
  analytics, and manage their own charging network.
- **EV drivers** discover compatible stations, manage vehicles, preferences,
  and favourites, search available 30-minute slots, and book or cancel
  simulated charging reservations.

Both roles talk to a LangGraph assistant that routes between domain knowledge
(RAG over pgvector), database-backed MCP tools, and ordinary answers.
Sensitive operations require an explicit, server-side confirmation.

The complete backend lives in [`backend/`](backend/README.md), including the
API reference, MCP tool inventory, booking rules, setup, and testing
instructions.

## Architecture

```text
React / API clients
        │ JWT
        ▼
FastAPI (auth, chat, owner, driver, bookings)
        │
        ├── LangGraph owner/driver workflows ── RAG (pgvector, role-scoped)
        │                                      └── LLM via OpenRouter
        │
        └── MCP client ── owner MCP server (9 tools)
                       └─ driver MCP server (15 tools)
                              │
                              ▼
                    PostgreSQL + pgvector
```

## Quick start (backend only)

```bash
cd backend
uv sync
cp .env.example .env          # set DATABASE_URL, JWT_SECRET_KEY, OPENROUTER_*
alembic upgrade head
python scripts/seed_stations.py
python scripts/ingest_docs.py
uvicorn app.main:app --reload
```

- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health
- Demo owner: `owner@chargemate.test / OwnerPass123!`
- Demo driver: `driver@chargemate.test / DriverPass123!`

## Docker

```bash
docker compose up --build
```

This starts PostgreSQL with pgvector, runs migrations, launches the owner and
driver MCP servers, and serves the API on port 8000.

## Tests

```bash
cd backend
pytest -v
```

The default suite uses isolated SQLite; PostgreSQL integration and booking
concurrency tests run when `TEST_DATABASE_URL` is set. See
[`backend/README.md`](backend/README.md) for details.

## Repository layout

- `backend/` — canonical application, migrations, seed knowledge, tests.
- `src/` — historical reference code, not imported by the backend.
