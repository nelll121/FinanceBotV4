"""Debts handlers with journal flow."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from bot.keyboards import build_main_keyboard, debt_type_keyboard, debts_menu_keyboard
from bot.services.sheets import SheetsService
from bot.services.users import get_user
from bot.states import DebtStates

router = Router(name="debts")

"""Debts handlers with journal flow."""

from __future__ import annotations
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from bot.keyboards import build_main_keyboard, debt_type_keyboard, debts_menu_keyboard
from bot.services.sheets import SheetsService
from bot.services.users import get_user
from bot.states import DebtStates
def _service_from_message(message: Message) -> SheetsService | None:
    if message.from_user is None:
        return None
    user = get_user(message.from_user.id)
    if user is None:
        return None
    sid = user.get("sheets_id")
    if not sid:
        return None
    return SheetsService(str(sid))


@router.message(F.text == "🤝 Долги")
async def debts_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Раздел долгов:", reply_markup=debts_menu_keyboard())


@router.message(F.text == "⬅️ Назад")
async def debts_back(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Возвращаемся в главное меню.", reply_markup=build_main_keyboard())


@router.message(F.text == "➕ Новый долг")
async def debt_create_start(message: Message, state: FSMContext) -> None:
    service = _service_from_message(message)
    if service is None:
        await message.answer("Сначала завершите /start и подключите таблицу.", reply_markup=build_main_keyboard())
        return

    await state.set_state(DebtStates.debt_type)
    await message.answer("Выберите тип долга:", reply_markup=debt_type_keyboard())


@router.message(DebtStates.debt_type)
async def debt_type_step(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text == "❌ Отмена":
        await state.clear()
        await message.answer("Операция отменена.", reply_markup=debts_menu_keyboard())
        return

    if text not in {"Мне должны", "Я должен"}:
        await message.answer("Выберите вариант кнопкой: 'Мне должны' или 'Я должен'.")
        return

    await state.update_data(debt_type=text)
    await state.set_state(DebtStates.name)
    await message.answer("Введите имя человека/организации:", reply_markup=ReplyKeyboardRemove())


@router.message(DebtStates.name)
async def debt_name_step(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("Введите корректное имя (минимум 2 символа).")
        return

    await state.update_data(name=name)
    await state.set_state(DebtStates.description)
    await message.answer("Введите описание долга (или '-' чтобы пропустить):")


@router.message(DebtStates.description)
async def debt_desc_step(message: Message, state: FSMContext) -> None:
    desc = (message.text or "").strip()
    if desc == "-":
        desc = ""
    await state.update_data(description=desc)
    await state.set_state(DebtStates.amount)
    await message.answer("Введите сумму долга:")


@router.message(DebtStates.amount)
async def debt_amount_step(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").replace(" ", "").replace(",", ".")
    try:
        amount = float(raw)
    except ValueError:
        await message.answer("Некорректная сумма. Введите число, например 35000")
        return

    if amount <= 0:
        await message.answer("Сумма должна быть больше 0")
        return

    await state.update_data(amount=amount)
    await state.set_state(DebtStates.due_date)
    await message.answer("Введите дату возврата в формате ДД.ММ.ГГГГ (или '-' чтобы пропустить):")


@router.message(DebtStates.due_date)
async def debt_due_step(message: Message, state: FSMContext) -> None:
    due = (message.text or "").strip()
    if due == "-":
        due = ""

    await state.update_data(due_date=due)
    await state.set_state(DebtStates.note)
    await message.answer("Введите заметку (или '-' чтобы пропустить):")


@router.message(DebtStates.note)
async def debt_note_step(message: Message, state: FSMContext) -> None:
    note = (message.text or "").strip()
    if note == "-":
        note = ""

    data = await state.get_data()
    service = _service_from_message(message)
    if service is None:
        await state.clear()
        await message.answer("Не удалось определить таблицу пользователя.", reply_markup=build_main_keyboard())
        return

    row = service.add_debt(
        debt_type=data["debt_type"],
        name=data["name"],
        amount=float(data["amount"]),
        description=data.get("description", ""),
        return_date=data.get("due_date") or None,
        note=note,
    )
    await state.clear()
    await message.answer(f"✅ Долг добавлен в журнал (строка {row}).", reply_markup=debts_menu_keyboard())


@router.message(F.text == "📋 Активные долги")
async def debts_active_list(message: Message) -> None:
    service = _service_from_message(message)
    if service is None:
        await message.answer("Сначала завершите /start и подключите таблицу.")
        return

    debts = service.get_active_debts()
    if not debts:
        await message.answer("Активных долгов нет.")
        return

    lines = ["📋 Активные долги:"]
    for debt in debts:
        lines.append(
            f"{debt['index']}: {debt['type']} | {debt['name']} | "
            f"{debt['amount']:.2f} | до {debt['return_date'] or 'не указано'}"
        )
    await message.answer("\n".join(lines))

@router.message(F.text == "✅ Вернуть долг")
async def debt_return_start(message: Message, state: FSMContext) -> None:
    service = _service_from_message(message)
    if service is None:
        await message.answer("Сначала завершите /start и подключите таблицу.")
        return

    debts = service.get_active_debts()
    if not debts:
        await message.answer("Активных долгов нет.")
        return

    lines = ["Введите индекс долга для полного возврата:"]
    for debt in debts:
        lines.append(f"{debt['index']}: {debt['type']} | {debt['name']} | {debt['amount']:.2f}")
    await state.set_state(DebtStates.return_index)
    await message.answer("\n".join(lines), reply_markup=ReplyKeyboardRemove())

@router.message(DebtStates.return_index)
async def debt_return_finish(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("Нужен числовой индекс из списка.")
        return

    service = _service_from_message(message)
    if service is None:
        await state.clear()
        await message.answer("Не удалось определить таблицу пользователя.", reply_markup=build_main_keyboard())
        return

    try:
        debt = service.return_debt_full(int(raw))
    except IndexError:
        await message.answer("Индекс вне диапазона. Попробуйте снова.")
        return

    await state.clear()
    await message.answer(
        f"✅ Долг '{debt['name']}' закрыт полностью и записан в ежедневные операции.",
        reply_markup=debts_menu_keyboard(),
    )


@router.message(F.text == "💸 Частичный возврат")
async def debt_partial_start(message: Message, state: FSMContext) -> None:
    service = _service_from_message(message)
    if service is None:
        await message.answer("Сначала завершите /start и подключите таблицу.")
        return

    debts = service.get_active_debts()
    if not debts:
        await message.answer("Активных долгов нет.")
        return

    lines = ["Введите индекс долга для частичного возврата:"]
    for debt in debts:
        lines.append(f"{debt['index']}: {debt['type']} | {debt['name']} | остаток {debt['amount']:.2f}")
    await state.set_state(DebtStates.partial_index)
    await message.answer("\n".join(lines), reply_markup=ReplyKeyboardRemove())

@router.message(DebtStates.partial_index)
async def debt_partial_index(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("Нужен числовой индекс из списка.")
        return

    await state.update_data(partial_index=int(raw))
    await state.set_state(DebtStates.partial_amount)
    await message.answer("Введите сумму частичного возврата:")


@router.message(DebtStates.partial_amount)
async def debt_partial_amount(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").replace(" ", "").replace(",", ".")
    try:
        paid = float(raw)
    except ValueError:
        await message.answer("Некорректная сумма. Введите число.")
        return

    service = _service_from_message(message)
    if service is None:
        await state.clear()
        await message.answer("Не удалось определить таблицу пользователя.", reply_markup=build_main_keyboard())
        return

    data = await state.get_data()
    try:
        debt = service.return_debt_partial(int(data["partial_index"]), paid)
    except IndexError:
        await message.answer("Индекс вне диапазона. Попробуйте снова.")
        return
    except ValueError:
        await message.answer("Сумма должна быть больше 0 и меньше остатка долга.")
        return

    await state.clear()
    await message.answer(
        f"✅ Частичный возврат сохранён. Остаток по долгу '{debt['name']}': {debt['amount']:.2f}",
        reply_markup=debts_menu_keyboard(),
    )
