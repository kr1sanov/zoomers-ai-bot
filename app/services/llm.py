"""Модуль взаимодействия с NVIDIA Integrate API (Mistral Medium 3.5)."""

from __future__ import annotations

import json
from typing import AsyncIterator, Optional

import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings

logger = structlog.get_logger(__name__)

TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=5.0)


def _build_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.nvidia_api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


@retry(
    retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def chat_complete(
    messages: list[dict[str, str]],
    system_prompt: Optional[str] = None,
) -> str:
    """
    Отправляет запрос к NVIDIA API и возвращает полный текст ответа.

    Args:
        messages: История диалога [{"role": "user"|"assistant", "content": "..."}]
        system_prompt: Системный промпт (переопределяет настройки по умолчанию)

    Returns:
        Текст ответа ассистента.
    """
    prompt = system_prompt or settings.system_prompt
    payload_messages = [{"role": "system", "content": prompt}] + messages

    payload = {
        "model": settings.model_name,
        "messages": payload_messages,
        "temperature": 0.7,
        "top_p": 1.0,
        "max_tokens": 4096,
        "stream": False,
    }

    logger.info(
        "llm.request",
        model=settings.model_name,
        messages_count=len(payload_messages),
    )

    async with httpx.AsyncClient(
        base_url=settings.nvidia_base_url,
        headers=_build_headers(),
        timeout=TIMEOUT,
    ) as client:
        response = await client.post("/chat/completions", json=payload)
        response.raise_for_status()

    data = response.json()
    try:
        content: str = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        logger.error("llm.parse_error", response=data)
        raise RuntimeError(f"Unexpected API response format: {data}") from exc

    tokens = data.get("usage", {})
    logger.info(
        "llm.response",
        prompt_tokens=tokens.get("prompt_tokens"),
        completion_tokens=tokens.get("completion_tokens"),
    )
    return content


async def chat_stream(
    messages: list[dict[str, str]],
    system_prompt: Optional[str] = None,
) -> AsyncIterator[str]:
    """
    Стриминг ответа от NVIDIA API.

    Yields:
        Текстовые чанки по мере получения от API.
    """
    prompt = system_prompt or settings.system_prompt
    payload_messages = [{"role": "system", "content": prompt}] + messages

    payload = {
        "model": settings.model_name,
        "messages": payload_messages,
        "temperature": 0.7,
        "max_tokens": 4096,
        "stream": True,
    }

    logger.info("llm.stream.start", model=settings.model_name)

    async with httpx.AsyncClient(
        base_url=settings.nvidia_base_url,
        headers={**_build_headers(), "Accept": "text/event-stream"},
        timeout=TIMEOUT,
    ) as client:
        async with client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data:"):
                    continue
                raw = line[5:].strip()
                if raw == "[DONE]":
                    break
                try:
                    chunk = json.loads(raw)
                    delta = chunk["choices"][0].get("delta", {})
                    if text_chunk := delta.get("content"):
                        yield text_chunk
                except Exception:
                    continue

    logger.info("llm.stream.done")
