"""Хэндлеры для администратора."""

from __future__ import annotations

import structlog
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.repository import ConversationRepository, UserRepository
from app.keyboards.admin import admin_menu_keyboard

router = Router(name="admin")
logger = structlog.get_logger(__name__)


class BroadcastState(StatesGroup):
    waiting_for_text = State()


def is_admin(user_id: int) -> bool:
    return user_id == settings.admin_id


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return
    await message.answer(
        "🛠 <b>Панель администратора</b>",
        reply_markup=admin_menu_keyboard(),
    )


@router.message(Command("users"))
async def cmd_users(message: Message, session: AsyncSession) -> None:
    if not is_admin(message.from_user.id):
        return
    repo = UserRepository(session)
    users = await repo.get_all(limit=20)
    count = await repo.count_users()
    lines = [f"👥 <b>Пользователи</b> (всего: {count})\n"]
    for u in users[:10]:
        uname = f"@{u.username}" if u.username else "—"
        lines.append(f"• <code>{u.id}</code> {u.first_name} {uname} | req: {u.total_requests}")
    await message.answer("\n".join(lines))


@router.message(Command("stats"))
async def cmd_stats_admin(message: Message, session: AsyncSession) -> None:
    if not is_admin(message.from_user.id):
        return
    user_repo = UserRepository(session)
    conv_repo = ConversationRepository(session)
    total_users = await user_repo.count_users()
    total_msgs = await conv_repo.count_messages()
    text_body = (
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Пользователей: <code>{total_users}</code>\n"
        f"💬 Сообщений: <code>{total_msgs}</code>"
    )
    await message.answer(text_body)


@router.message(Command("health"))
async def cmd_health(message: Message, session: AsyncSession) -> None:
    if not is_admin(message.from_user.id):
        return
    try:
        await session.execute(text("SELECT 1"))
        db_status = "✅ OK"
    except Exception as e:
        db_status = f"❌ {e}"
    body = (
        f"🏥 <b>Health Check</b>\n\n"
        f"🗄 Database: {db_status}\n"
        f"🤖 Model: <code>{settings.model_name}</code>\n"
        "🌐 NVIDIA API: configured"
    )
    await message.answer(body)


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return
    await state.set_state(BroadcastState.waiting_for_text)
    await message.answer("📢 Введите текст рассылки:")


@router.message(BroadcastState.waiting_for_text)
async def process_broadcast(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    await state.clear()
    user_repo = UserRepository(session)
    users = await user_repo.get_all(limit=10000)
    sent = failed = 0
    for u in users:
        try:
            await message.bot.send_message(u.id, message.text)
            sent += 1
        except Exception:
            failed += 1
    await message.answer(
        f"📢 Рассылка завершена.\n✅ Отправлено: {sent}\n❌ Ошибок: {failed}"
    )


@router.callback_query(F.data == "admin_stats")
async def cb_admin_stats(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()
    await cmd_stats_admin(callback.message, session)


@router.callback_query(F.data == "admin_users")
async def cb_admin_users(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()
    await cmd_users(callback.message, session)


@router.callback_query(F.data == "admin_health")
async def cb_admin_health(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()
    await cmd_health(callback.message, session)


@router.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await cmd_broadcast(callback.message, state)
