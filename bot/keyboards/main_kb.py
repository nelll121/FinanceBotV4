"""Main menu keyboards."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

MAIN_MENU_TEXT = "🏠 Главное меню"


def build_main_keyboard() -> ReplyKeyboardMarkup:
    """Build FinanceBot v2 main menu keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💸 Расход"), KeyboardButton(text="💰 Доход")],
            [KeyboardButton(text="🤝 Долги"), KeyboardButton(text="🎯 Накопления")],
            [KeyboardButton(text="📊 Сводка"), KeyboardButton(text="🤖 ИИ советник")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие…",
    )
