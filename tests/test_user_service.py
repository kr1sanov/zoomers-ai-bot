"""Тесты сервисного слоя."""

import pytest

from app.services.user_service import UserService


@pytest.mark.asyncio
async def test_ensure_user(session):
    svc = UserService(session)
    user = await svc.ensure_user(user_id=1001, first_name="Service")
    assert user.id == 1001


@pytest.mark.asyncio
async def test_get_history_empty(session):
    svc = UserService(session)
    await svc.ensure_user(user_id=1002, first_name="Hist")
    history = await svc.get_history(1002)
    assert history == []


@pytest.mark.asyncio
async def test_save_and_get_history(session):
    svc = UserService(session)
    await svc.ensure_user(user_id=1003, first_name="Save")
    await svc.save_exchange(1003, "Question", "Answer")
    history = await svc.get_history(1003)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_reset_history(session):
    svc = UserService(session)
    await svc.ensure_user(user_id=1004, first_name="Res")
    await svc.save_exchange(1004, "Q", "A")
    await svc.reset_history(1004)
    history = await svc.get_history(1004)
    assert history == []
