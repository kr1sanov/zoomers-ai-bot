"""Конфигурация приложения через Pydantic Settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Все настройки приложения, считываемые из .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Telegram
    bot_token: str = Field(..., description="Telegram Bot API token")
    admin_id: int = Field(..., description="Telegram ID администратора")

    # Database
    database_url: str = Field(..., description="PostgreSQL DSN (asyncpg)")

    # NVIDIA / LLM
    nvidia_api_key: str = Field(..., description="NVIDIA Integrate API key")
    model_name: str = Field(
        default="mistralai/mistral-medium-3.5-128b",
        description="Имя модели",
    )
    nvidia_base_url: str = Field(
        default="https://integrate.api.nvidia.com/v1",
        description="Base URL NVIDIA API",
    )

    # Logging
    log_level: str = Field(default="INFO", description="Уровень логирования")

    # Throttling
    throttle_rate: float = Field(
        default=1.0, description="Минимальный интервал между сообщениями (сек)"
    )

    # Limits
    max_history_length: int = Field(
        default=20, description="Максимальное число сообщений в истории"
    )
    max_daily_requests: int = Field(
        default=100, description="Лимит запросов к LLM в сутки на пользователя"
    )

    # Feature flags
    feature_voice: bool = Field(default=False, description="Голосовые сообщения")
    feature_images: bool = Field(default=False, description="Обработка изображений")
    feature_rag: bool = Field(default=False, description="RAG / документы")
    feature_web_search: bool = Field(default=False, description="Веб-поиск")
    feature_multi_model: bool = Field(default=False, description="Несколько моделей")

    # System prompt
    system_prompt: str = Field(
        default=(
            "Ты — Zoomers AI, умный, дружелюбный ассистент для поколения Z. "
            "Отвечай кратко, по делу, используй Markdown-форматирование. "
            "Будь честен: если не знаешь — скажи об этом."
        ),
        description="Системный промпт по умолчанию",
    )


settings = Settings()
