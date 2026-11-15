# GenAI Platform — Backend

Member 4 deliverable: GenAI foundation, shared LangGraph runtime, MCP tool
layer, authenticated chat API, RAG over pgvector, and the offline-first AI
evaluation suite.

## Architecture

```
FastAPI client
      |
      v
POST /chat                (app/api/routes/chat.py)
      |  JWT -> AuthContext
      v
build_agent_graph(role)   (app/agents/shared/runtime.py)
      |   route -> [rag] -> (complete | invoke_tools) -> respond
      |                       confirm/reject gate
      v
MCPToolRegistry           (app/mcp/client.py)
      |  streamable HTTP -> SSE -> stdio fallback
      |  auth_context injected per call (LLM cannot spoof it)
      v
Member 2 / Member 3 MCP servers

RAG: knowledge_base/{owner,driver}/*.txt
     -> scripts/ingest_docs.py -> knowledge_documents + knowledge_embeddings
     (pgvector, HNSW cosine index) -> retrieve_for_role
```

## Environment variables (`backend/.env`)

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | – | Neon Postgres (pooled endpoint). Powers RAG storage and the chat API's message persistence. |
| `OPENROUTER_API_KEY` | – | OpenRouter key used for all LLM calls. |
| `OPENROUTER_MODEL` | `nvidia/nemotron-3.5-super-vl:free` | Any OpenRouter chat-completion model works; per-model fallbacks (`llm/models.py`) adapt to model quirks. |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | Override only when proxying. |
| `JWT_SECRET_KEY` | – | HS256 signing key shared with the auth lane. |
| `MCP_OWNER_SERVER_URL` / `MCP_DRIVER_SERVER_URL` | – | Streamable-HTTP MCP endpoints for Member 2/3 servers. Empty means stdio-only (dev registries). |
| `RAG_EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Local sentence-transformers model (384 dims, no API cost). |
| `RAG_CHUNK_SIZE` / `RAG_CHUNK_OVERLAP` | `1000` / `150` | Token-aware chunking (`app/rag/chunker.py`). |
| `RAG_TOP_K` / `RAG_MIN_SCORE` | `4` / `0.35` | Retrieval knobs for `retrieve_for_role`. |
| `knowledge_base_dir`, `owner_knowledge_dir`, `driver_knowledge_dir` | `knowledge_base/...` | Source documents for ingestion. |

## Prompt configuration

Prompts live in `app/llm/prompts.py`. `PROMPT_VERSION = "1.0.0"` is the
content version; `ACTIVE_PROMPT_VERSION = "v1"` selects the active variant
(`get_prompt(version)`). Role routing prompts (owner/driver) list the exact
tool sets from the team's tool-allocation doc, so routing decisions and tool
selection follow Member 1's schema and Member 2/3's tool names.

Changing prompts is data-only: bump `PROMPT_VERSION`, keep `ACTIVE_PROMPT_VERSION`
pointing at the intended variant, and rerun `scripts/evaluate_ai.py` offline.

## Graph flow (`app/agents/shared/nodes.py`)

1. **check_pending_confirmation** – if a booking confirmation is pending:
   an explicit `confirm`/`reject` action runs the registered tool directly
   or cancels (the LLM is bypassed for the gated call); anything else keeps
   the proposal pending and routes normally.
2. **route_request** – LLM classifies the message as `tool`, `general`, or
   `rag`; falls back to `general` on invalid output.
3. **rag_context** (only for `rag` and only when a retriever is registered)
   – `retrieve_for_role` enforces role-scoped documents and `min_score`.
4. **complete / invoke_tools** – bounded (6-round) tool loop.
   `invoke_tools` injects `auth_context` into every call and strips any
   LLM-supplied `auth_context` from arguments (identity spoofing guard).
5. **Confirmation contract** – a domain tool may return a
   `confirmation_request` payload (`tool`, `arguments`, `action`, `summary`).
   `invoke_tools` relays it as `pending_confirmation`; the graph refuses the
   proposal's confirm tool while awaiting an explicit user action — including
   within the same tool loop in which the proposal was produced. The chat API
   persists the proposal as a `confirmation_request` message so the frontend
   can render Approve/Reject controls.

## MCP connection setup

- Production/deployed: set `MCP_OWNER_SERVER_URL` / `MCP_DRIVER_SERVER_URL`
  to the streamable-HTTP endpoint of each server. The client tries
  streamable HTTP, then SSE, then reports `503 mcp_unavailable`.
- Local development with an empty URL: `MCPToolRegistry` falls back to a
  stdio transport; tests exercise this path against
  `tests/mcp_test_server.py` (FastMCP).
- Connections are opened per operation (`_use_session`): anyio cancel
  scopes require same-task entry/exit, so there is no pooled cross-task
  session. `aclose()` exists for lifecycle parity but is a no-op.
- Identity: `AuthContext` is appended server-side as the reserved
  `auth_context` argument; it is hidden from tool schemas exposed to the LLM
  and stripped from LLM-provided arguments.

## RAG ingestion and re-indexing

```powershell
.venv\Scripts\python.exe scripts\ingest_docs.py            # whole tree
.venv\Scripts\python.exe scripts\ingest_docs.py --reindex  # force replace
.venv\Scripts\python.exe scripts\ingest_docs.py --file path\to\doc.md --role driver
```

Ingestion is idempotent by content hash (`indexed` vs `skipped`).
Migration `0002_rag_knowledge` creates the pgvector tables and the HNSW
cosine index; the migration chain is stamped in `alembic_version`.

## Running the evaluation suite

```powershell
.venv\Scripts\python.exe -m pytest -q                 # full suite
.venv\Scripts\python.exe -m pytest tests/test_evaluation.py -q
.venv\Scripts\python.exe scripts\evaluate_ai.py                      # 17 cases
.venv\Scripts\python.exe scripts\evaluate_ai.py --category confirmation --json out\eval_report.json
```

- `app/evaluation/cases.py` defines 17 cases across routing, tool selection,
  RAG grounding, refusals, follow-ups, confirmation flow, and security
  (bypass attempts, prompt injection, role confusion, out-of-role tools).
- `app/evaluation/runner.py` replays them through the real graphs with a
  scripted tool registry (`ScriptedToolRegistry` mirrors the agreed tool
  schemas) and real `retrieve_for_role`, then applies per-category checks.
- Offline mode uses `tests/fakes.py::FakeLLMClient` (no API calls, no cost).
- Live mode reads `OPENROUTER_API_KEY`; the OpenRouter free tier is limited
  to 50 free-model requests/day, and a full 17-case run spends roughly 2–4
  requests per case — split runs with `--category` if you hit the cap.
- Exit code is 1 when any case fails; `--json` writes a machine-readable
  report with per-case statuses, tools called, and failures.

## Model support

Any OpenRouter chat model can be set via `OPENROUTER_MODEL`. Tool-call
parsing is normalized in `app/llm/client.py` / `models.py` so per-provider
response shapes (tool_calls, JSON tool arguments, content-only fallbacks)
are handled consistently; invalid routing output falls back to `general`
instead of failing the request.
