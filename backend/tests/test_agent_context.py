
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.agents.shared.context import (
    ConversationNotFoundError,
    load_history,
    save_exchange,
)
from app.database.base import Base
from app.models import Conversation, Message, User
from app.models.conversation import MessageRole
from app.models.user import UserRole


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def users(db):
    owner = User(
        name="Owner One",
        email="owner1@example.com",
        password_hash="hash",
        role=UserRole.OWNER,
    )

    other = User(
        name="Owner Two",
        email="owner2@example.com",
        password_hash="hash",
        role=UserRole.OWNER,
    )

    db.add_all([owner, other])
    db.commit()

    return owner, other


def create_conversation(db, user):
    conversation = Conversation(user_id=user.id, title="Chat")
    db.add(conversation)
    db.commit()

    return conversation


def test_load_history_returns_ordered_messages(db, users):
    owner, _ = users
    conversation = create_conversation(db, owner)

    save_exchange(db, owner.id, conversation.id, "Show my stations", "You have 3 stations.")
    save_exchange(db, owner.id, conversation.id, "Which made most revenue?", "Station A.")

    history = load_history(db, owner.id, conversation.id)

    assert [entry["role"] for entry in history] == ["user", "assistant", "user", "assistant"]
    assert history[0]["content"] == "Show my stations"
    assert history[-1]["content"] == "Station A."


def test_load_history_excludes_tool_messages(db, users):
    owner, _ = users
    conversation = create_conversation(db, owner)

    save_exchange(db, owner.id, conversation.id, "Hi", "Hello!")

    db.add(
        Message(
            conversation_id=conversation.id,
            role=MessageRole.TOOL,
            content='{"status": "ok"}',
        )
    )
    db.commit()

    history = load_history(db, owner.id, conversation.id)

    assert [entry["role"] for entry in history] == ["user", "assistant"]


def test_load_history_respects_limit(db, users):
    owner, _ = users
    conversation = create_conversation(db, owner)

    for index in range(5):
        save_exchange(
            db,
            owner.id,
            conversation.id,
            f"Question {index}",
            f"Answer {index}",
        )

    history = load_history(db, owner.id, conversation.id, limit=2)

    assert len(history) == 2
    assert history[0]["content"] == "Question 4"
    assert history[-1]["content"] == "Answer 4"


def test_load_history_enforces_ownership(db, users):
    owner, other = users
    conversation = create_conversation(db, owner)

    with pytest.raises(ConversationNotFoundError):
        load_history(db, other.id, conversation.id)


def test_save_exchange_enforces_ownership(db, users):
    owner, other = users
    conversation = create_conversation(db, owner)

    with pytest.raises(ConversationNotFoundError):
        save_exchange(db, other.id, conversation.id, "Hi", "Hello")

    assert db.query(Message).count() == 0


def test_save_exchange_persists_metadata(db, users):
    owner, _ = users
    conversation = create_conversation(db, owner)

    saved = save_exchange(
        db,
        owner.id,
        conversation.id,
        "Show my stations",
        "You have 3 stations.",
        assistant_metadata={"route": "tool", "tool_results": [{"tool": "get_owner_stations"}]},
        assistant_message_type="structured",
    )

    assert saved.message_type == "structured"
    assert saved.metadata_json["route"] == "tool"
