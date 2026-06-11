"""Точка входа Zoomers AI Bot."""

import asyncio

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.database.engine import AsyncSessionFactory, engine
from app.database.models import Base
from app.handlers import admin, user
from app.logger import setup_logging
from app.middlewares.db import DbSessionMiddleware
from app.middlewares.throttle import ThrottlingMiddleware

logger = structlog.get_logger(__name__)


async def on_startup(bot: Bot) -> None:
    """Создаёт таблицы при старте (если не используется Alembic)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("bot.startup", username="@zooomers_bot")


async def on_shutdown(bot: Bot) -> None:
    """Корректно завершает соединения."""
    await engine.dispose()
    logger.info("bot.shutdown")


async def main() -> None:
    setup_logging(settings.log_level)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=MemoryStorage())

    # Middlewares
    dp.message.middleware(ThrottlingMiddleware(rate=settings.throttle_rate))
    dp.message.middleware(DbSessionMiddleware(AsyncSessionFactory))
    dp.callback_query.middleware(DbSessionMiddleware(AsyncSessionFactory))

    # Роутеры (admin первым — он проверяет is_admin)
    dp.include_router(admin.router)
    dp.include_router(user.router)

    # Lifecycle hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.info("bot.starting", model=settings.model_name)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
