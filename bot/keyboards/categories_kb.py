"""Dynamic categories keyboard builder."""

from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup



def build_categories_keyboard(categories: list[str], *, include_cancel: bool = True) -> ReplyKeyboardMarkup:
    rows: list[list[KeyboardButton]] = []
    for category in categories:
        rows.append([KeyboardButton(text=category)])

    if include_cancel:
        rows.append([KeyboardButton(text="❌ Отмена")])

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите категорию…",
    )
