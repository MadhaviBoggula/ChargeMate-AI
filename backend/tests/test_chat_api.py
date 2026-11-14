
from uuid import uuid4

import pytest

from app.api.routes import chat as chat_module
from app.llm.client import LLMError


def register_and_login(client, email, role="driver"):
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test User",
            "email": email,
            "password": "TestPassword123",
            "role": role,
        },
    )

    assert registration.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "TestPassword123",
        },
    )

    assert login.status_code == 200

    return login.json()["access_token"]


def default_result(**overrides):
    result = {
        "response": "All done.",
        "route": "general",
        "tool_results": [],
        "rag_context": [],
        "pending_confirmation": None,
    }

    result.update(overrides)

    return result


@pytest.fixture
def invoke_calls(monkeypatch):
    calls = []
    scripted = []

    async def fake_invoke_graph(**kwargs):
        calls.append(kwargs)

        item = scripted.pop(0) if scripted else default_result()

        if isinstance(item, Exception):
            raise item

        return item

    monkeypatch.setattr(
        chat_module,
        "invoke_graph",
        fake_invoke_graph,
    )

    return calls, scripted


def test_chat_requires_authentication(client, invoke_calls):
    response = client.post(
        "/api/v1/chat",
        json={"message": "Show my stations"},
    )

    assert response.status_code == 401


def test_chat_creates_conversation_and_persists_messages(
    client,
    invoke_calls,
):
    calls, _ = invoke_calls
    token = register_and_login(client, "chat1@example.com")

    response = client.post(
        "/api/v1/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Show my stations"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["response"] == "All done."
    assert data["route"] == "general"
    assert data["conversation_id"]
    assert data["message_id"]

    detail = client.get(
        f"/api/v1/conversations/{data['conversation_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert detail.status_code == 200

    messages = detail.json()["messages"]

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Show my stations"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["message_type"] == "text"
    assert messages[1]["metadata_json"]["route"] == "general"


def test_chat_passes_verified_role_to_graph(client, invoke_calls):
    calls, _ = invoke_calls
    owner_token = register_and_login(client, "chatowner@example.com", role="owner")
    driver_token = register_and_login(client, "chatdriver@example.com", role="driver")

    client.post(
        "/api/v1/chat",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"message": "Revenue this month?"},
    )

    client.post(
        "/api/v1/chat",
        headers={"Authorization": f"Bearer {driver_token}"},
        json={"message": "Find stations in Kukatpally"},
    )

    assert calls[0]["role"] == "owner"
    assert calls[1]["role"] == "driver"


def test_chat_unknown_conversation_returns_404(client, invoke_calls):
    invoke_calls
    token = register_and_login(client, "chat2@example.com")

    response = client.post(
        "/api/v1/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Hi", "conversation_id": str(uuid4())},
    )

    assert response.status_code == 404


def test_chat_llm_error_returns_502(client, invoke_calls):
    _, scripted = invoke_calls
    scripted.append(LLMError("provider down"))

    token = register_and_login(client, "chat3@example.com")

    response = client.post(
        "/api/v1/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Show my stations"},
    )

    assert response.status_code == 502


def test_confirmation_without_conversation_returns_400(client, invoke_calls):
    invoke_calls
    token = register_and_login(client, "chat4@example.com")

    response = client.post(
        "/api/v1/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Book it", "confirmation_action": "confirm"},
    )

    assert response.status_code == 400


def test_confirmation_without_pending_returns_409(client, invoke_calls):
    invoke_calls
    token = register_and_login(client, "chat5@example.com")

    created = client.post(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Booking chat"},
    )

    conversation_id = created.json()["id"]

    response = client.post(
        "/api/v1/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "Book it",
            "conversation_id": conversation_id,
            "confirmation_action": "confirm",
        },
    )

    assert response.status_code == 409


def test_confirmation_flow_passes_pending_proposal(client, invoke_calls):
    calls, scripted = invoke_calls
    token = register_and_login(client, "chat6@example.com")

    pending = {
        "action": "confirm_booking",
        "proposal_id": "prop-123",
        "tool": "confirm_booking",
        "arguments": {"proposal_id": "prop-123"},
        "summary": {"station": "Kukatpally", "duration_minutes": 30},
    }

    scripted.append(default_result(pending_confirmation=pending))

    first = client.post(
        "/api/v1/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Book the 6 PM slot"},
    )

    assert first.status_code == 200

    first_data = first.json()

    assert first_data["pending_confirmation"] == pending

    conversation_id = first_data["conversation_id"]

    scripted.append(default_result(response="Booking confirmed."))

    second = client.post(
        "/api/v1/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "Confirm",
            "conversation_id": conversation_id,
            "confirmation_action": "confirm",
        },
    )

    assert second.status_code == 200
    assert second.json()["response"] == "Booking confirmed."

    assert len(calls) == 2

    confirm_call = calls[1]

    assert confirm_call["confirmation_action"] == "confirm"
    assert confirm_call["pending_confirmation"] == pending

    detail = client.get(
        f"/api/v1/conversations/{conversation_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    messages = detail.json()["messages"]

    confirmation_messages = [
        message
        for message in messages
        if message["message_type"] == "confirmation_request"
    ]

    assert len(confirmation_messages) == 1
    assert (
        confirmation_messages[0]["metadata_json"]["pending_confirmation"]
        == pending
    )
