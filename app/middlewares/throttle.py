"""Middleware для ограничения частоты запросов."""

from __future__ import annotations

import time
from typing import Any, Awaitable, Callable

import structlog
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

logger = structlog.get_logger(__name__)


class ThrottlingMiddleware(BaseMiddleware):
    """Rate-limiter: не более одного сообщения каждые `rate` секунд."""

    def __init__(self, rate: float = 1.0) -> None:
        self.rate = rate
        self._last_call: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user_id = event.from_user.id if event.from_user else None
        if user_id is None:
            return await handler(event, data)

        now = time.monotonic()
        last = self._last_call.get(user_id, 0.0)
        if now - last < self.rate:
            logger.info("throttle.blocked", user_id=user_id)
            await event.answer("⏳ Слишком быстро! Подождите немного.")
            return None

        self._last_call[user_id] = now
        return await handler(event, data)
