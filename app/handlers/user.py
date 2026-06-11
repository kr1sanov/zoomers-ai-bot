"""Хэндлеры для пользовательских команд и сообщений."""

from __future__ import annotations

import structlog
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repository import ConversationRepository, UserRepository
from app.keyboards.user import confirm_reset_keyboard, main_menu_keyboard
from app.services.llm import chat_complete
from app.services.user_service import UserService
from app.utils.formatting import split_long_message

router = Router(name="user")
logger = structlog.get_logger(__name__)


@router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession) -> None:
    """Приветствие и регистрация пользователя."""
    user = message.from_user
    svc = UserService(session)
    await svc.ensure_user(
        user_id=user.id,
        first_name=user.first_name,
        username=user.username,
        last_name=user.last_name,
        language_code=user.language_code,
    )
    text = (
        f"👋 Привет, <b>{user.first_name}</b>!\n\n"
        "Я — <b>Zoomers AI</b>, твой ИИ-ассистент на базе Mistral.\n\n"
        "Просто напиши мне что-нибудь, и я отвечу. "
        "Используй /help, чтобы узнать все возможности."
    )
    await message.answer(text, reply_markup=main_menu_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Справка по командам."""
    text = (
        "📖 <b>Справка по командам</b>\n\n"
        "/start — начать работу\n"
        "/help — эта справка\n"
        "/reset — сбросить историю диалога\n"
        "/profile — информация о тебе\n"
        "/stats — твоя статистика\n\n"
        "💡 Просто пиши сообщения — я буду отвечать!"
    )
    await message.answer(text)


@router.message(Command("reset"))
async def cmd_reset(message: Message) -> None:
    """Запрос подтверждения сброса истории."""
    await message.answer(
        "⚠️ Ты уверен, что хочешь сбросить историю диалога?",
        reply_markup=confirm_reset_keyboard(),
    )


@router.message(Command("profile"))
async def cmd_profile(message: Message, session: AsyncSession) -> None:
    """Профиль пользователя."""
    user_repo = UserRepository(session)
    db_user = await user_repo.get_by_id(message.from_user.id)
    if db_user is None:
        await message.answer("Профиль не найден. Используй /start.")
        return
    text = (
        f"👤 <b>Профиль</b>\n\n"
        f"🆔 ID: <code>{db_user.id}</code>\n"
        f"📛 Имя: {db_user.first_name}\n"
        f"🔖 Username: @{db_user.username or '—'}\n"
        f"📅 Регистрация: {db_user.registered_at.strftime('%d.%m.%Y')}\n"
        f"⏰ Последняя активность: {db_user.last_active_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"📨 Запросов всего: <code>{db_user.total_requests}</code>\n"
        f"📬 Запросов сегодня: <code>{db_user.daily_requests}</code>"
    )
    await message.answer(text)


@router.message(Command("stats"))
async def cmd_stats(message: Message, session: AsyncSession) -> None:
    """Статистика пользователя."""
    user_repo = UserRepository(session)
    db_user = await user_repo.get_by_id(message.from_user.id)
    if db_user is None:
        await message.answer("Профиль не найден. Используй /start.")
        return
    text = (
        f"📊 <b>Твоя статистика</b>\n\n"
        f"💬 Запросов всего: <code>{db_user.total_requests}</code>\n"
        f"📅 Запросов сегодня: <code>{db_user.daily_requests}</code>"
    )
    await message.answer(text)


@router.callback_query(F.data == "confirm_reset")
async def cb_confirm_reset(callback: CallbackQuery, session: AsyncSession) -> None:
    svc = UserService(session)
    await svc.reset_history(callback.from_user.id)
    await callback.message.edit_text("✅ История диалога сброшена!")
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cb_cancel(callback: CallbackQuery) -> None:
    await callback.message.edit_text("❌ Действие отменено.")
    await callback.answer()


@router.callback_query(F.data == "help")
async def cb_help(callback: CallbackQuery) -> None:
    await callback.answer()
    await cmd_help(callback.message)


@router.callback_query(F.data == "profile")
async def cb_profile(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()
    await cmd_profile(callback.message, session)


@router.callback_query(F.data == "stats")
async def cb_stats(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()
    await cmd_stats(callback.message, session)


@router.callback_query(F.data == "reset")
async def cb_reset(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "⚠️ Сбросить историю диалога?",
        reply_markup=confirm_reset_keyboard(),
    )


@router.message(F.text)
async def handle_message(message: Message, session: AsyncSession) -> None:
    """Основной хэндлер: отправляет сообщение в LLM, сохраняет и возвращает ответ."""
    user = message.from_user
    svc = UserService(session)

    await svc.ensure_user(
        user_id=user.id,
        first_name=user.first_name,
        username=user.username,
    )

    if not await svc.check_daily_limit(user.id):
        await message.answer("⛔ Дневной лимит запросов исчерпан. Попробуй завтра!")
        return

    await message.bot.send_chat_action(message.chat.id, action="typing")

    history = await svc.get_history(user.id)
    history.append({"role": "user", "content": message.text})

    try:
        response_text = await chat_complete(history)
    except Exception as exc:
        logger.error("llm.error", user_id=user.id, error=str(exc))
        await message.answer(
            "😔 Произошла ошибка при обращении к ИИ. Попробуй ещё раз позже."
        )
        return

    await svc.save_exchange(user.id, message.text, response_text)

    for part in split_long_message(response_text):
        try:
            await message.answer(part, parse_mode="HTML")
        except Exception:
            await message.answer(part)
