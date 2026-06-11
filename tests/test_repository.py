"""Тесты репозитория пользователей и диалогов."""

import pytest

from app.database.models import MessageRole
from app.database.repository import ConversationRepository, UserRepository


@pytest.mark.asyncio
async def test_create_user(session):
    repo = UserRepository(session)
    user = await repo.create_or_update(
        user_id=111, first_name="Test", username="testuser"
    )
    assert user.id == 111
    assert user.first_name == "Test"
    assert user.total_requests == 0


@pytest.mark.asyncio
async def test_update_user(session):
    repo = UserRepository(session)
    await repo.create_or_update(user_id=222, first_name="Old")
    updated = await repo.create_or_update(user_id=222, first_name="New")
    assert updated.first_name == "New"


@pytest.mark.asyncio
async def test_increment_requests(session):
    repo = UserRepository(session)
    await repo.create_or_update(user_id=333, first_name="Inc")
    await repo.increment_requests(333)
    user = await repo.get_by_id(333)
    assert user.total_requests == 1
    assert user.daily_requests == 1


@pytest.mark.asyncio
async def test_conversation_flow(session):
    user_repo = UserRepository(session)
    conv_repo = ConversationRepository(session)
    await user_repo.create_or_update(user_id=444, first_name="Conv")
    conv = await conv_repo.create(444)
    assert conv.id is not None
    await conv_repo.add_message(conv.id, MessageRole.USER, "Hello")
    await conv_repo.add_message(conv.id, MessageRole.ASSISTANT, "Hi!")
    history = await conv_repo.get_history(conv.id)
    assert len(history) == 2
    assert history[0].role == MessageRole.USER
    assert history[1].role == MessageRole.ASSISTANT


@pytest.mark.asyncio
async def test_deactivate_conversations(session):
    user_repo = UserRepository(session)
    conv_repo = ConversationRepository(session)
    await user_repo.create_or_update(user_id=555, first_name="Reset")
    await conv_repo.create(555)
    await conv_repo.deactivate_all(555)
    active = await conv_repo.get_active(555)
    assert active is None
