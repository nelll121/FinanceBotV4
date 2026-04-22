"""Entry point for FinanceBot v2."""

from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from loguru import logger

from bot.config import BOT_TOKEN
from bot.handlers import setup_routers
from bot.services.scheduler import setup_scheduler


async def _set_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="help", description="Помощь"),
        ]
    )


async def run() -> None:
    """Launch polling loop."""
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is required")

    from aiogram.client.default import DefaultBotProperties

bot = Bot(
    BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
    dp = Dispatcher()
    dp.include_router(setup_routers())

    await _set_commands(bot)
    setup_scheduler(bot)
    logger.info("FinanceBot v2 started")
    await dp.start_polling(bot)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
