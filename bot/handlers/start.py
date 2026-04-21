"""Startup, registration and help handlers."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from bot.config import ADMIN_USER_ID, TIMEZONE
from bot.keyboards import build_main_keyboard
from bot.services.drive import create_from_template
from bot.services.users import UserRecord, get_user, is_registered, save_user, update_user, user_exists

router = Router(name="start")


class StartRegistrationStates(StatesGroup):
    waiting_name = State()
    waiting_email = State()


def _is_admin(user_id: int) -> bool:
    if not ADMIN_USER_ID:
        return False
    return str(user_id) == str(ADMIN_USER_ID)


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    """Register user and show main menu."""
    tg_user = message.from_user
    if tg_user is None:
        return

    user_id = tg_user.id

    if user_exists(user_id) and is_registered(user_id):
        await state.clear()
        await message.answer(
            f"С возвращением, {tg_user.full_name}! 👋\nТаблица уже подключена.",
            reply_markup=build_main_keyboard(),
        )
        return

    if not user_exists(user_id):
        save_user(
            UserRecord(
                user_id=user_id,
                name=tg_user.full_name,
                timezone=TIMEZONE,
                is_admin=_is_admin(user_id),
                ai_access=_is_admin(user_id),
            )
        )

    await state.set_state(StartRegistrationStates.waiting_name)
    await message.answer("Давай завершим регистрацию.\nВведите ваше имя:")


@router.message(StartRegistrationStates.waiting_name)
async def register_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("Имя слишком короткое. Введите корректное имя.")
        return

    await state.update_data(name=name)
    await state.set_state(StartRegistrationStates.waiting_email)
    await message.answer("Введите email Google аккаунта для выдачи доступа к таблице:")


@router.message(StartRegistrationStates.waiting_email)
async def register_email(message: Message, state: FSMContext) -> None:
    tg_user = message.from_user
    if tg_user is None:
        return

    email = (message.text or "").strip()
    if "@" not in email or "." not in email.split("@")[-1]:
        await message.answer("Некорректный email. Попробуйте ещё раз.")
        return

    data = await state.get_data()

    await message.answer("Создаю вашу таблицу на основе шаблона, это может занять до 10 секунд…")
    try:
        sheets_id = await create_from_template(email)
    except Exception:
        await message.answer(
            "Не удалось создать таблицу. Проверьте email и права сервисного аккаунта, затем повторите /start."
        )
        await state.clear()
        return

    update_user(
        tg_user.id,
        name=data.get("name", tg_user.full_name),
        sheets_id=sheets_id,
        email=email,
    )
    await state.clear()

    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheets_id}"
    await message.answer(
        "✅ Регистрация завершена!\n"
        f"Ваша таблица: {sheet_url}",
        reply_markup=build_main_keyboard(),
    )


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    """Show available commands."""
    await message.answer(
        "Доступные команды:\n"
        "/start — регистрация/перезапуск\n"
        "/help — помощь\n"
        "/users — список пользователей (admin)\n"
        "/grant <id> — выдать AI доступ (admin)\n"
        "/revoke <id> — забрать AI доступ (admin)",
        reply_markup=build_main_keyboard(),
    )
