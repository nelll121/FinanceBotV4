"""Claude AI service wrapper."""

from __future__ import annotations

import time
from typing import Any

import anthropic
from loguru import logger

from bot.config import ANTHROPIC_API_KEY
from bot.services.users import get_api_key

SYSTEM_PROMPT = (
    "Ты личный финансовый советник. "
    "Отвечай простым текстом без markdown. "
    "Короткие абзацы. Язык: русский. "
    "Давай конкретные рекомендации с цифрами."
)

MODEL = "claude-3-5-haiku-latest"


def _resolve_api_key(user_id: int | str) -> str:
    user_key = get_api_key(user_id)
    if user_key is None:
        raise ValueError("NO_API_KEY")

    if user_key.strip():
        return user_key.strip()

    if ANTHROPIC_API_KEY:
        return ANTHROPIC_API_KEY

    raise ValueError("NO_API_KEY")


def _get_client(user_id: int | str) -> anthropic.Anthropic:
    key = _resolve_api_key(user_id)
    return anthropic.Anthropic(api_key=key)


def _message_text(response) -> str:
    return "".join(block.text for block in response.content if hasattr(block, "text")).strip()


def _send_with_retry(client: anthropic.Anthropic, *, system: str, messages: list[dict], max_tokens: int) -> str:
    last_exc: Exception | None = None
    for attempt in range(1, 4):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
            )
            return _message_text(response)
        except Exception as exc:
            last_exc = exc
            logger.warning("Anthropic call failed attempt={}: {}", attempt, exc)
            if attempt < 3:
                time.sleep(0.4 * attempt)

    raise RuntimeError(f"Anthropic request failed after retries: {last_exc}")


async def categorize_expense(user_id: int | str, text: str, categories: list[str]) -> str | None:
    """Predict expense category from free-text description."""
    if not categories:
        return None

    client = _get_client(user_id)
    prompt = (
        "Выбери одну категорию из списка или ответь NONE.\n"
        f"Категории: {', '.join(categories)}\n"
        f"Текст расхода: {text}\n"
        "Ответ только одним словом/фразой без пояснений."
    )

    answer = _send_with_retry(
        client,
        max_tokens=30,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    if not answer or answer.upper() == "NONE":
        return None

    for category in categories:
        if answer.lower() == category.lower():
            return category
    return None


async def get_ai_response(
    user_id: int | str,
    context: dict[str, Any],
    history: list[dict[str, str]],
    message: str,
) -> str:
    """Get conversational financial advice from Claude."""
    client = _get_client(user_id)

    context_text = (
        f"Контекст пользователя: {context}. "
        "Используй это как факты для анализа и рекомендаций."
    )

    messages = history[-10:] + [{"role": "user", "content": message}]

    text = _send_with_retry(
        client,
        max_tokens=500,
        system=SYSTEM_PROMPT + "\n" + context_text,
        messages=messages,
    )
    return text or "Не удалось получить ответ от ИИ."


async def generate_morning_summary(user_id: int | str, context: dict[str, Any]) -> str:
    """Generate morning summary with recommendations."""
    client = _get_client(user_id)
    prompt = (
        "Сделай утреннюю финансовую сводку на 3-5 предложений. "
        "Учитывай контекст и дай 1-2 конкретных совета с цифрами. "
        f"Контекст: {context}"
    )

    return _send_with_retry(
        client,
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )


async def generate_evening_summary(user_id: int | str, context: dict[str, Any]) -> str:
    """Generate evening summary with day-end advice."""
    client = _get_client(user_id)
    prompt = (
        "Сделай вечернюю сводку на 3-5 предложений. "
        "Оцени день и дай 1 совет на завтра. "
        f"Контекст: {context}"
    )

    return _send_with_retry(
        client,
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
