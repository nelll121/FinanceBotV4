"""Income handlers with FSM flow and Google Sheets write."""

from __future__ import annotations

from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from bot.keyboards import build_categories_keyboard, build_main_keyboard
from bot.services.sheets import IncomeEntry, SheetsService, normalize_categories
from bot.services.users import get_user
from bot.states import IncomeStates

router = Router(name="income")


@router.message(F.text == "💰 Доход")
async def income_start(message: Message, state: FSMContext) -> None:
    user = get_user(message.from_user.id) if message.from_user else None
    if user is None or not user.get("sheets_id"):
        await message.answer("Сначала подключите Google таблицу (sheets_id отсутствует).")
        return

    service = SheetsService(user["sheets_id"])
    categories = normalize_categories(service.get_income_categories())
    if not categories:
        categories = ["Прочее"]

    await state.set_state(IncomeStates.category)
    await message.answer(
        "Выберите категорию дохода:",
        reply_markup=build_categories_keyboard(categories),
    )


@router.message(IncomeStates.category)
async def income_category(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text == "❌ Отмена":
        await state.clear()
        await message.answer("Операция отменена.", reply_markup=build_main_keyboard())
        return

    await state.update_data(category=text)
    await state.set_state(IncomeStates.amount)
    await message.answer("Введите сумму дохода:", reply_markup=ReplyKeyboardRemove())


@router.message(IncomeStates.amount)
async def income_amount(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").replace(" ", "").replace(",", ".")
    try:
        amount = float(raw)
    except ValueError:
        await message.answer("Некорректная сумма. Введите число, например 50000")
        return

    if amount <= 0:
        await message.answer("Сумма должна быть больше 0.")
        return

    await state.update_data(amount=amount)
    await state.set_state(IncomeStates.description)
    await message.answer("Введите описание дохода:")


@router.message(IncomeStates.description)
async def income_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=(message.text or "").strip())
    await state.set_state(IncomeStates.note)
    await message.answer("Введите заметку (или '-' чтобы пропустить):")


@router.message(IncomeStates.note)
async def income_note(message: Message, state: FSMContext) -> None:
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
    entry = IncomeEntry(
        date=datetime.now().strftime("%d.%m.%Y"),
        description=data.get("description", ""),
        category=data.get("category", "Прочее"),
        amount=float(data.get("amount", 0)),
        note=note,
    )

    row = service.append_income(entry)
    await state.clear()
    await message.answer(
        f"✅ Доход сохранён в строку {row} ({entry.amount:.2f}).",
        reply_markup=build_main_keyboard(),
    )
