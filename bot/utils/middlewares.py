"""Bot middlewares."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message
from loguru import logger

from bot.services.users import is_registered, user_exists


class AccessMiddleware(BaseMiddleware):
    """Block unregistered users except during /start flow."""

    ALLOWED_COMMANDS = {"/start", "/help"}

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        # Allow non-message events through
        if not isinstance(event, Message):
            return await handler(event, data)

        # Allow /start and /help always
        text = (event.text or "").strip()
        if any(text.startswith(cmd) for cmd in self.ALLOWED_COMMANDS):
            return await handler(event, data)

        # Allow if FSM state is active (mid-registration)
        fsm = data.get("state")
        if fsm is not None:
            current_state = await fsm.get_state()
            if current_state is not None:
                return await handler(event, data)

        # Check registration
        user_id = event.from_user.id if event.from_user else None
        if user_id and user_exists(user_id) and is_registered(user_id):
            return await handler(event, data)

        # Not registered
        if event.from_user:
            await event.answer(
                "Сначала выполните /start для регистрации."
            )
        return None


class LoggingMiddleware(BaseMiddleware):
    """Log all incoming messages."""

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.from_user:
            logger.info(
                "[{}] {}: {}",
                event.from_user.id,
                event.from_user.full_name,
                (event.text or "")[:80],
            )
        return await handler(event, data)
