"""Expenses handlers with FSM flow and Google Sheets write."""

from __future__ import annotations

from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from bot.keyboards import build_categories_keyboard, build_main_keyboard
from bot.services.sheets import ExpenseEntry, SheetsService, normalize_categories
from bot.services.users import get_user
from bot.states import ExpenseStates

router = Router(name="expenses")


@router.message(F.text == "💸 Расход")
async def expense_start(message: Message, state: FSMContext) -> None:
    user = get_user(message.from_user.id) if message.from_user else None
    if user is None or not user.get("sheets_id"):
        await message.answer("Сначала подключите Google таблицу (sheets_id отсутствует).")
        return

    service = SheetsService(user["sheets_id"])
    categories = normalize_categories(service.get_expense_categories())
    if not categories:
        categories = ["Прочее"]

    await state.set_state(ExpenseStates.category)
    await message.answer(
        "Выберите категорию расхода:",
        reply_markup=build_categories_keyboard(categories),
    )


@router.message(ExpenseStates.category)
async def expense_category(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text == "❌ Отмена":
        await state.clear()
        await message.answer("Операция отменена.", reply_markup=build_main_keyboard())
        return

    await state.update_data(category=text)
    await state.set_state(ExpenseStates.amount)
    await message.answer("Введите сумму расхода (например: 12500):", reply_markup=ReplyKeyboardRemove())


@router.message(ExpenseStates.amount)
async def expense_amount(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").replace(" ", "").replace(",", ".")
    try:
        amount = float(raw)
    except ValueError:
        await message.answer("Некорректная сумма. Введите число, например 12500")
        return

    if amount <= 0:
        await message.answer("Сумма должна быть больше 0.")
        return

    await state.update_data(amount=amount)
    await state.set_state(ExpenseStates.description)
    await message.answer("Введите описание расхода:")


@router.message(ExpenseStates.description)
async def expense_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=(message.text or "").strip())
    await state.set_state(ExpenseStates.note)
    await message.answer("Введите заметку (или '-' чтобы пропустить):")


@router.message(ExpenseStates.note)
async def expense_note(message: Message, state: FSMContext) -> None:
    note = (message.text or "").strip()
    if note == "-":
        note = ""

    data = await state.get_data()
    user = get_user(message.from_user.id) if message.from_user else None
    if user is None or not user.get("sheets_id"):
        await state.clear()
        await message.answer("Не удалось найти подключённую таблицу.", reply_markup=build_main_keyboard())
        return

    service = SheetsService(user["sheets_id"])
    entry = ExpenseEntry(
        date=datetime.now().strftime("%d.%m.%Y"),
        description=data.get("description", ""),
        category=data.get("category", "Прочее"),
        amount=float(data.get("amount", 0)),
        note=note,
    )

    row = service.append_expense(entry)
    await state.clear()
    await message.answer(
        f"✅ Расход сохранён в строку {row} ({entry.amount:.2f}).",
        reply_markup=build_main_keyboard(),
    )
