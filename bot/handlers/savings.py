"""Savings and goals handlers."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from bot.keyboards import build_main_keyboard
from bot.services.sheets import SheetsService
from bot.services.users import get_user
from bot.states import SavingsStates

router = Router(name="savings")

"""Savings and goals handlers."""

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from bot.keyboards import build_main_keyboard
from bot.services.sheets import SheetsService
from bot.services.users import get_user
from bot.states import SavingsStates
def _service(message: Message) -> SheetsService | None:
    if message.from_user is None:
        return None
    user = get_user(message.from_user.id)
    if user is None or not user.get("sheets_id"):
        return None
    return SheetsService(str(user["sheets_id"]))


def _menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📌 Мои цели")],
            [KeyboardButton(text="➕ Новая цель")],
            [KeyboardButton(text="💳 Пополнить цель")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True,
    )


@router.message(F.text == "🎯 Накопления")
async def savings_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Раздел накоплений:", reply_markup=_menu_kb())


@router.message(F.text == "📌 Мои цели")
async def savings_list(message: Message) -> None:
    service = _service(message)
    if service is None:
        await message.answer("Сначала завершите /start и подключите таблицу.")
        return

    goals = service.get_savings_goals()
    if not goals:
        await message.answer("Пока нет целей. Нажмите '➕ Новая цель'.")
        return

    lines = ["🎯 Ваши цели:"]
    for g in goals:
        lines.append(
            f"• {g['name']}: {g['current_amount']:.2f}/{g['target_amount']:.2f} ({g['percent']:.1f}%)"
        )
    await message.answer("\n".join(lines))

@router.message(F.text == "➕ Новая цель")
async def savings_new_start(message: Message, state: FSMContext) -> None:
    if _service(message) is None:
        await message.answer("Сначала завершите /start и подключите таблицу.")
        return

    await state.set_state(SavingsStates.goal_name)
    await message.answer("Введите название цели:")


@router.message(SavingsStates.goal_name)
async def savings_goal_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("Название слишком короткое.")
        return

    await state.update_data(goal_name=name)
    await state.set_state(SavingsStates.goal_amount)
    await message.answer("Введите сумму цели:")


@router.message(SavingsStates.goal_amount)
async def savings_goal_amount(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").replace(" ", "").replace(",", ".")
    try:
        target = float(raw)
    except ValueError:
        await message.answer("Некорректная сумма. Введите число.")
        return

    if target <= 0:
        await message.answer("Сумма должна быть больше 0.")
        return

    data = await state.get_data()
    service = _service(message)
    if service is None:
        await state.clear()
        await message.answer("Не удалось определить таблицу.", reply_markup=build_main_keyboard())
        return

    row = service.add_savings_goal(data["goal_name"], target)
    await state.clear()
    await message.answer(f"✅ Цель добавлена (строка {row}).", reply_markup=_menu_kb())


@router.message(F.text == "💳 Пополнить цель")
async def savings_topup_start(message: Message, state: FSMContext) -> None:
    service = _service(message)
    if service is None:
        await message.answer("Сначала завершите /start и подключите таблицу.")
        return

    goals = service.get_savings_goals()
    if not goals:
        await message.answer("Сначала создайте хотя бы одну цель.")
        return

    await state.set_state(SavingsStates.topup_goal_name)
    names = ", ".join(g["name"] for g in goals)
    await message.answer(f"Введите название цели для пополнения:\n{names}")


@router.message(SavingsStates.topup_goal_name, F.text == "⬅️ Назад")
async def savings_back_during_state(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Возвращаемся в раздел накоплений.", reply_markup=_menu_kb())


@router.message(SavingsStates.topup_goal_name)
async def savings_topup_goal_name(message: Message, state: FSMContext) -> None:
    await state.update_data(goal_name=(message.text or "").strip())
    await state.set_state(SavingsStates.topup_amount)
    await message.answer("Введите сумму пополнения:")


@router.message(SavingsStates.topup_amount)
async def savings_topup_amount(message: Message, state: FSMContext) -> None:
    data = await state.get_data()

    raw = (message.text or "").replace(" ", "").replace(",", ".")
    try:
        add_amount = float(raw)
    except ValueError:
        await message.answer("Некорректная сумма. Введите число.")
        return

    if add_amount <= 0:
        await message.answer("Сумма должна быть больше 0.")
        return

    service = _service(message)
    if service is None:
        await state.clear()
        await message.answer("Не удалось определить таблицу.", reply_markup=build_main_keyboard())
        return

    try:
        updated = service.update_savings_goal(data["goal_name"], add_amount)
    except ValueError:
        await message.answer("Цель не найдена. Проверьте название и попробуйте снова.")
        return

    await state.clear()
    await message.answer(
        f"✅ Цель '{updated['name']}' пополнена. Теперь: "
        f"{updated['current_amount']:.2f}/{updated['target_amount']:.2f} ({updated['percent']:.1f}%).",
        reply_markup=_menu_kb(),
    )


@router.message(F.text == "⬅️ Назад")
async def savings_back(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Возвращаемся в главное меню.", reply_markup=build_main_keyboard())
