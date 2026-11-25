
# ChargeMate AI Backend

FastAPI backend for the ChargeMate AI electric vehicle charging platform.

## Technology Stack

- Python
- FastAPI
- SQLAlchemy 2
- PostgreSQL (Neon)
- Alembic
- Pydantic
- JWT Authentication
- Pytest

## Project Structure

```text
backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   └── deps.py
│   ├── core/
│   ├── database/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── migrations/
│   └── versions/
├── tests/
├── .env.example
├── alembic.ini
└── pyproject.toml
```

## Setup

### 1. Install dependencies

```bash
uv sync
```

### 2. Configure environment variables

Create a `.env` file in the backend directory using `.env.example` as a reference.

Configure:

- DATABASE_URL
- JWT_SECRET_KEY
- Application settings

Never commit the actual `.env` file or share its secrets.

### 3. Run the application

```bash
uv run uvicorn app.main:app --reload
```

Backend URL:

http://127.0.0.1:8000

API documentation:

http://127.0.0.1:8000/docs

## API Endpoints

### Authentication

| Method | Endpoint |
|---|---|
| POST | /api/v1/auth/register |
| POST | /api/v1/auth/login |
| GET | /api/v1/auth/me |

### Conversations

| Method | Endpoint |
|---|---|
| POST | /api/v1/conversations |
| GET | /api/v1/conversations |
| GET | /api/v1/conversations/{conversation_id} |
| POST | /api/v1/conversations/{conversation_id}/messages |

Conversation endpoints require JWT authentication.
Users can access only their own conversations.

### Health

| Method | Endpoint |
|---|---|
| GET | /health |
| GET | /ready |

## Database

The backend uses PostgreSQL through Neon.

Current core tables:

- users
- conversations
- messages

Database migrations are managed using Alembic.

Before creating or applying migrations, review the migration and coordinate schema changes with the relevant team members.

## Run Tests

Run the complete test suite:

```bash
uv run pytest -v
```

Run conversation tests only:

```bash
uv run pytest tests/test_conversations_api.py -v
```

Tests use an in-memory SQLite database and do not modify the Neon database.

## Member 1 Responsibilities

- Backend foundation
- Database configuration
- Shared SQLAlchemy conventions
- Alembic configuration
- Authentication and JWT
- Conversation and message persistence
- Backend testing and documentation
