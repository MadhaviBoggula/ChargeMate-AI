# ChargeMate AI — Backend

FastAPI modular monolith. GenAI platform (OpenRouter, LangGraph, MCP client, RAG)
scaffolded by Member 4; foundation/domain lanes stubbed for Members 1–3.

## Setup

```powershell
py -3.12 -m venv backend/.venv          # Python 3.12 required (torch wheels)
cd backend
.\.venv\Scripts\pip install -r requirements.txt
copy ..\.env.example ..\.env            # then fill in real values (repo root)
.\.venv\Scripts\python scripts\setup_db.py      # verify Neon + enable pgvector
.\.venv\Scripts\python -m uvicorn app.main:app --reload
.\.venv\Scripts\python scripts\smoke_genai.py   # LLM + embeddings check
.\.venv\Scripts\python -m pytest
```

- `.env` lives at the **repo root** (never committed); backend reads it via pydantic-settings.
- Endpoints: `GET /health`, `GET /ready`, `POST /api/v1/chat` (401 until auth lands), docs at `/docs`.

## Module ownership (task allocation v1.0)

| Path | Owner |
|---|---|
| `app/core`, `app/database`, `app/auth`, `app/api/auth.py`, `app/api/conversations.py` | Member 1 |
| `app/mcp/owner_server.py` + owner domain models/services | Member 2 |
| `app/mcp/driver_server.py` + driver/booking models/services | Member 3 |
| `app/llm`, `app/agents/shared`, `app/agents/owner|driver` (framework), `app/mcp/client.py`, `app/rag`, `app/api/chat.py` | Member 4 |

## Key facts

- **LLM**: OpenRouter (OpenAI-compatible) via `langchain-openai`; model/temp/timeout/retries/max tool rounds from `.env`.
- **Embeddings**: local `sentence-transformers` (`all-MiniLM-L6-v2`, 384 dims), CPU, no API key; downloads on first use.
- **pgvector 0.8.7** already enabled on the Neon branch (`scripts/setup_db.py` is idempotent).
- **MCP**: client manager degrades gracefully while `MCP_OWNER_SERVER_URL` / `MCP_DRIVER_SERVER_URL` are empty; identity always injected from trusted JWT context, never from the LLM.
- **Graphs**: role routing (`general`/`tool`/`rag`) → bounded tool loop (≤ `MAX_TOOL_CALL_ROUNDS`) → grounded response; `pending_confirmation` state reserved for booking confirmation pause/resume. Owner/driver graphs are default-composed placeholders until Members 2/3 register domain nodes.
- **RAG**: `app/rag/ingest.py` (pypdf/docx/txt → chunk 1000/150 → role-tagged), `app/rag/retriever.py` (pgvector, role filter, top-k 4, min score 0.35). Drop documents in `knowledge_base/owner|driver/`.
- Alembic is wired to settings; **no migrations exist yet** — Member 1 authors the first; domain owners author their own.
