"""Настройки приложения через pydantic-settings и feature flags."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FeatureFlags(BaseSettings):
    """Флаги фич для управления функциональностью без деплоя."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    enable_voice: bool = Field(default=False, description="Голосовые сообщения")
    enable_images: bool = Field(default=False, description="Генерация изображений")
    enable_rag: bool = Field(default=False, description="RAG (поиск по документам)")
    enable_web_search: bool = Field(default=False, description="Веб-поиск")
    enable_multi_model: bool = Field(default=False, description="Несколько LLM-моделей")


class Settings(BaseSettings):
    """Основные настройки бота."""

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_file_encoding="utf-8"
    )

    # Telegram
    bot_token: str = Field(..., description="Токен Telegram-бота")
    admin_id: int = Field(..., description="Telegram ID администратора")

    # Database
    database_url: str = Field(..., description="PostgreSQL DSN (asyncpg)")

    # NVIDIA / LLM
    nvidia_api_key: str = Field(..., description="NVIDIA Integrate API key")
    model_name: str = Field(
        default="mistralai/mistral-medium-3.5-128b",
        description="Имя LLM-модели",
    )

    # Limits
    daily_request_limit: int = Field(default=100, description="Лимит запросов в день")
    max_history_messages: int = Field(
        default=20, description="Максимум сообщений в истории"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Уровень логирования")

    @property
    def features(self) -> FeatureFlags:
        """Возвращает объект feature flags."""
        return FeatureFlags()


settings = Settings()
