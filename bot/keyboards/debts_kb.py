"""Debts section keyboards."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def debts_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Новый долг")],
            [KeyboardButton(text="📋 Активные долги")],
            [KeyboardButton(text="✅ Вернуть долг")],
            [KeyboardButton(text="💸 Частичный возврат")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True,
    )


def debt_type_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Мне должны")],
            [KeyboardButton(text="Я должен")],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
