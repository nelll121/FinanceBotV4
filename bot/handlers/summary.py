"""Summary handlers."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from bot.keyboards import build_main_keyboard
from bot.services.sheets import SheetsService
from bot.services.users import get_user
from bot.utils.formatters import fmt_money, progress_bar

router = Router(name="summary")


@router.message(F.text == "📊 Сводка")
async def summary_month(message: Message) -> None:
    if message.from_user is None:
        return

    user = get_user(message.from_user.id)
    if user is None or not user.get("sheets_id"):
        await message.answer(
            "Сначала завершите /start и подключите таблицу.",
            reply_markup=build_main_keyboard()
        )
        return

    service = SheetsService(str(user["sheets_id"]))
    s = service.get_month_summary()

    pct = s.get("savings_percent", 0)
    bar = progress_bar(pct, 100)

    text = (
        f"📊 {s.get('month', '')} {s.get('year', '')}\n"
        f"{'═' * 22}\n\n"
        f"💚 Доход:     {fmt_money(s.get('income', 0))}\n"
        f"❤️  Расход:    {fmt_money(s.get('expense', 0))}\n"
        f"💼 Баланс:    {fmt_money(s.get('balance', 0))}\n\n"
        f"📈 Накоплено: {pct:.0f}%\n{bar}"
    )
    await message.answer(text, reply_markup=build_main_keyboard())
