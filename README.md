# 🤖 Zoomers AI Bot

[![CI/CD](https://github.com/kr1sanov/zoomers-ai-bot/actions/workflows/deploy.yml/badge.svg)](https://github.com/kr1sanov/zoomers-ai-bot/actions)

Telegram AI-бот [@zooomers_bot](https://t.me/zooomers_bot) на Python 3.12 + aiogram 3.x,  
работающий на модели `mistralai/mistral-medium-3.5-128b` через NVIDIA Integrate API.

## ⚡ Быстрый старт

```bash
git clone https://github.com/kr1sanov/zoomers-ai-bot
cd zoomers-ai-bot
cp .env.example .env
# Заполни .env своими значениями
docker compose up -d
```

## 🔑 Переменные окружения

| Переменная | Описание |
|---|---|
| `BOT_TOKEN` | Токен Telegram-бота от @BotFather |
| `ADMIN_ID` | Telegram ID администратора |
| `DATABASE_URL` | PostgreSQL DSN (asyncpg формат) |
| `NVIDIA_API_KEY` | API-ключ NVIDIA Integrate |
| `MODEL_NAME` | Имя LLM (по умолч. `mistral-medium-3.5-128b`) |
| `LOG_LEVEL` | `INFO` / `DEBUG` / `WARNING` |
| `THROTTLE_RATE` | Мин. интервал между сообщениями (сек, по умолч. `1.0`) |
| `MAX_DAILY_REQUESTS` | Дневной лимит запросов на пользователя (по умолч. `100`) |

## 🧩 Фич-флаги (в .env)

```env
FEATURE_VOICE=false       # Голосовые сообщения
FEATURE_IMAGES=false      # Обработка изображений
FEATURE_RAG=false         # RAG / документы
FEATURE_WEB_SEARCH=false  # Веб-поиск
FEATURE_MULTI_MODEL=false # Несколько моделей
```

## 📦 Структура проекта

```
app/
├── handlers/     # Telegram-хэндлеры (user, admin)
├── services/     # LLM-клиент и бизнес-логика
├── database/     # Модели, репозитории, движок
├── middlewares/  # DB-сессия, троттлинг
├── keyboards/    # InlineKeyboard
└── utils/        # Форматирование
migrations/       # Alembic-миграции
tests/            # Unit / integration тесты
```

## 🛠 Команды бота

### Пользователь
| Команда | Описание |
|---|---|
| `/start` | Регистрация и приветствие |
| `/help` | Список команд |
| `/reset` | Сбросить историю диалога |
| `/profile` | Профиль пользователя |
| `/stats` | Личная статистика |

### Администратор
| Команда | Описание |
|---|---|
| `/admin` | Панель администратора |
| `/users` | Список пользователей |
| `/stats` | Общая статистика |
| `/health` | Статус БД и API |
| `/broadcast` | Рассылка всем пользователям |

## 🚀 Деплой на VPS

```bash
# 1. Установить Docker
curl -fsSL https://get.docker.com | sh

# 2. Клонировать репозиторий
git clone https://github.com/kr1sanov/zoomers-ai-bot
cd zoomers-ai-bot

# 3. Настроить переменные окружения
cp .env.example .env
nano .env

# 4. Запустить
docker compose up -d

# 5. Смотреть логи
docker compose logs -f bot
```

## 🗄 Миграции (опционально)

Таблицы создаются автоматически при старте бота.  
Для управления миграциями через Alembic:

```bash
# Создать новую миграцию
alembic revision --autogenerate -m "описание"

# Применить миграции
alembic upgrade head
```

## 🧪 Запуск тестов

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/ -v
```

## 🏗 Технологический стек

- **Python 3.12** + **aiogram 3.x**
- **SQLAlchemy 2.0** + **asyncpg** + **Alembic**
- **PostgreSQL 16**
- **structlog** для логирования
- **httpx** + **tenacity** для LLM-клиента
- **Pydantic Settings** для конфигурации
- **Docker** + **Docker Compose**
- **GitHub Actions** для CI/CD
