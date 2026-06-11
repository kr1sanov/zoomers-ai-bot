"""Точка входа Zoomers AI Bot."""
import asyncio
import logging

import structlog
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.logger import setup_logging
from app.database.engine import create_db_and_tables
from app.handlers.user import router as user_router
from app.handlers.admin import router as admin_router
from app.middlewares.db import DbSessionMiddleware
from app.middlewares.throttle import ThrottleMiddleware


async def main() -> None:
    """Инициализация и запуск бота."""
    setup_logging()
    log = structlog.get_logger("main")

    await create_db_and_tables()
    log.info("database.ready")

    bot = Bot(token=settings.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Middlewares
    dp.message.middleware(DbSessionMiddleware())
    dp.message.middleware(ThrottleMiddleware())

    # Routers
    dp.include_router(user_router)
    dp.include_router(admin_router)

    log.info("bot.starting", username="@zooomers_bot")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
