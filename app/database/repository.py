"""Репозитории для работы с базой данных."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional, Sequence

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Conversation, Message, MessageRole, User, UserSettings

logger = structlog.get_logger(__name__)


class UserRepository:
    """CRUD-операции для модели User."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        user_id: int,
        first_name: str,
        username: Optional[str] = None,
        last_name: Optional[str] = None,
        language_code: Optional[str] = None,
    ) -> User:
        user = await self.get_by_id(user_id)
        now = datetime.now(timezone.utc)
        if user is None:
            user = User(
                id=user_id,
                first_name=first_name,
                username=username,
                last_name=last_name,
                language_code=language_code,
                last_active_at=now,
            )
            self.session.add(user)
            logger.info("user.created", user_id=user_id)
        else:
            user.first_name = first_name
            user.username = username
            user.last_name = last_name
            user.last_active_at = now
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def increment_requests(self, user_id: int) -> None:
        """Увеличивает счётчики; сбрасывает дневной при смене дня."""
        user = await self.get_by_id(user_id)
        if user is None:
            return
        today = date.today()
        if user.last_request_date and user.last_request_date.date() != today:
            user.daily_requests = 0
        user.daily_requests += 1
        user.total_requests += 1
        user.last_request_date = datetime.now(timezone.utc)
        await self.session.commit()

    async def count_users(self) -> int:
        result = await self.session.execute(select(func.count(User.id)))
        return result.scalar_one()

    async def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[User]:
        result = await self.session.execute(
            select(User).order_by(User.registered_at.desc()).limit(limit).offset(offset)
        )
        return result.scalars().all()


class ConversationRepository:
    """CRUD-операции для Conversation и Message."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active(self, user_id: int) -> Optional[Conversation]:
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id, Conversation.is_active == True)  # noqa: E712
            .options(selectinload(Conversation.messages))
            .order_by(Conversation.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: int, title: Optional[str] = None) -> Conversation:
        conv = Conversation(user_id=user_id, title=title)
        self.session.add(conv)
        await self.session.commit()
        await self.session.refresh(conv)
        return conv

    async def deactivate_all(self, user_id: int) -> None:
        await self.session.execute(
            update(Conversation)
            .where(Conversation.user_id == user_id)
            .values(is_active=False)
        )
        await self.session.commit()
        logger.info("conversations.reset", user_id=user_id)

    async def add_message(
        self,
        conversation_id: int,
        role: MessageRole,
        content: str,
        tokens_used: Optional[int] = None,
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tokens_used=tokens_used,
        )
        self.session.add(msg)
        await self.session.commit()
        return msg

    async def count_messages(self) -> int:
        result = await self.session.execute(select(func.count(Message.id)))
        return result.scalar_one()

    async def get_history(
        self, conversation_id: int, limit: int = 20
    ) -> Sequence[Message]:
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        return list(reversed(result.scalars().all()))
