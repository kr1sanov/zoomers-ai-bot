"""Утилиты форматирования сообщений."""

from __future__ import annotations


def escape_md(text: str) -> str:
    """Экранирует спецсимволы для MarkdownV2."""
    special = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in special else c for c in text)


def split_long_message(text: str, max_length: int = 4096) -> list[str]:
    """Разбивает длинный текст на части для отправки в Telegram."""
    if len(text) <= max_length:
        return [text]
    parts: list[str] = []
    while text:
        parts.append(text[:max_length])
        text = text[max_length:]
    return parts


def format_stats(
    total_users: int,
    total_messages: int,
    daily_requests: int = 0,
) -> str:
    """Форматирует статистику для отображения."""
    return (
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Пользователей: <code>{total_users}</code>\n"
        f"💬 Сообщений всего: <code>{total_messages}</code>\n"
        f"📅 Запросов сегодня: <code>{daily_requests}</code>"
    )
