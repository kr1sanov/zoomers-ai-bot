"""Сервисный слой для работы с пользователями."""

from __future__ import annotations

from typing import Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import MessageRole
from app.database.repository import ConversationRepository, UserRepository

logger = structlog.get_logger(__name__)


class UserService:
    """Бизнес-логика для пользователей и диалогов."""

    def __init__(self, session: AsyncSession) -> None:
        self.user_repo = UserRepository(session)
        self.conv_repo = ConversationRepository(session)

    async def ensure_user(
        self,
        user_id: int,
        first_name: str,
        username: Optional[str] = None,
        last_name: Optional[str] = None,
        language_code: Optional[str] = None,
    ):
        """Регистрирует нового или обновляет существующего пользователя."""
        return await self.user_repo.create_or_update(
            user_id=user_id,
            first_name=first_name,
            username=username,
            last_name=last_name,
            language_code=language_code,
        )

    async def check_daily_limit(self, user_id: int) -> bool:
        """Возвращает True, если лимит ещё не исчерпан."""
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            return True
        return user.daily_requests < settings.max_daily_requests

    async def get_or_create_conversation(self, user_id: int):
        conv = await self.conv_repo.get_active(user_id)
        if conv is None:
            conv = await self.conv_repo.create(user_id)
        return conv

    async def get_history(self, user_id: int) -> list[dict[str, str]]:
        """Возвращает историю текущего диалога в формате для LLM."""
        conv = await self.conv_repo.get_active(user_id)
        if conv is None:
            return []
        messages = await self.conv_repo.get_history(
            conv.id, limit=settings.max_history_length
        )
        return [{"role": m.role.value, "content": m.content} for m in messages]

    async def save_exchange(
        self, user_id: int, user_text: str, assistant_text: str
    ) -> None:
        """Сохраняет пару сообщений пользователь/ассистент."""
        conv = await self.get_or_create_conversation(user_id)
        await self.conv_repo.add_message(conv.id, MessageRole.USER, user_text)
        await self.conv_repo.add_message(conv.id, MessageRole.ASSISTANT, assistant_text)
        await self.user_repo.increment_requests(user_id)

    async def reset_history(self, user_id: int) -> None:
        """Сбрасывает всю историю диалогов."""
        await self.conv_repo.deactivate_all(user_id)
