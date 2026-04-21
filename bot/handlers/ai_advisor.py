"""AI advisor chat handlers."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Deque

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger

from bot.keyboards import build_main_keyboard
from bot.services.ai_service import get_ai_response
from bot.services.sheets import SheetsService
from bot.services.users import get_user

router = Router(name="ai_advisor")

"""AI advisor chat handlers."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Deque
from aiogram.filters import Command
from loguru import logger
from bot.keyboards import build_main_keyboard
from bot.services.ai_service import get_ai_response
from bot.services.sheets import SheetsService
from bot.services.users import get_user

CHAT_HISTORY: dict[int, Deque[dict[str, str]]] = defaultdict(lambda: deque(maxlen=10))
AI_MODE_USERS: set[int] = set()


async def ai_prefs_show(message: Message) -> None:
    if message.from_user is None:
        return
    user = get_user(message.from_user.id)
    if user is None or not user.get("sheets_id"):
        await message.answer("Сначала завершите /start и подключите таблицу.")
        return

    try:
        service = SheetsService(str(user["sheets_id"]))
        prefs = service.get_ai_preferences()
    except Exception as exc:
        logger.exception("ai_prefs_show failed: {}", exc)
        await message.answer("Не удалось получить ИИ-предпочтения. Попробуйте позже.")
        return

    if not prefs:
        await message.answer("ИИ-предпочтения пока не заданы.")
        return

    lines = ["⚙️ ИИ-предпочтения:"]
    for k, v in prefs.items():
        lines.append(f"• {k}: {v}")
    await message.answer("\n".join(lines))

@router.message(Command("ai_pref"))
async def ai_prefs_set(message: Message) -> None:
    if message.from_user is None:
        return

    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Использование: /ai_pref <ключ> <значение>")
        return

    user = get_user(message.from_user.id)
    if user is None or not user.get("sheets_id"):
        await message.answer("Сначала завершите /start и подключите таблицу.")
        return

    key, value = parts[1], parts[2]
    try:
        service = SheetsService(str(user["sheets_id"]))
        ok = service.save_ai_preference(key, value)
    except Exception as exc:
        logger.exception("ai_prefs_set failed: {}", exc)
        await message.answer("Не удалось сохранить предпочтение. Попробуйте позже.")
        return

    if ok:
        await message.answer(f"✅ Предпочтение сохранено: {key}={value}")
    else:
        await message.answer("Не удалось сохранить предпочтение.")


@router.message(Command("ai_pref_clear"))
async def ai_prefs_clear(message: Message) -> None:
    if message.from_user is None:
        return

    user = get_user(message.from_user.id)
    if user is None or not user.get("sheets_id"):
        await message.answer("Сначала завершите /start и подключите таблицу.")
        return

    try:
        service = SheetsService(str(user["sheets_id"]))
        service.clear_ai_preferences()
    except Exception as exc:
        logger.exception("ai_prefs_clear failed: {}", exc)
        await message.answer("Не удалось очистить ИИ-предпочтения.")
        return

    await message.answer("✅ ИИ-предпочтения очищены.")


@router.message(F.text == "🤖 ИИ советник")
async def ai_start(message: Message) -> None:
    if message.from_user is None:
        return

    user = get_user(message.from_user.id)
    if user is None:
        await message.answer("Сначала завершите /start и подключите таблицу.")
        return

    if not user.get("ai_access") and not user.get("api_key"):
        await message.answer(
            "ИИ пока недоступен для вас. Попросите администратора выдать доступ через /grant.",
            reply_markup=build_main_keyboard(),
        )
        return

    AI_MODE_USERS.add(message.from_user.id)
    await message.answer(
        "Режим ИИ-советника включён. Напишите вопрос по вашим финансам.\n"
        "Чтобы выйти: отправьте 'выход' или нажмите кнопку другого раздела.",
    )


@router.message(F.text.lower() == "выход")
async def ai_exit(message: Message) -> None:
    if message.from_user is None:
        return

    if message.from_user.id in AI_MODE_USERS:
        AI_MODE_USERS.discard(message.from_user.id)
        await message.answer("Режим ИИ-советника выключен.", reply_markup=build_main_keyboard())


@router.message()
async def ai_chat_handler(message: Message) -> None:
    if message.from_user is None:
        return

    user_id = message.from_user.id
    if user_id not in AI_MODE_USERS:
        return

    user = get_user(user_id)
    if user is None or not user.get("sheets_id"):
        await message.answer("Не найдена привязанная таблица. Выполните /start.")
        return

    try:
        service = SheetsService(str(user["sheets_id"]))
        context = service.get_full_context()

        history = list(CHAT_HISTORY[user_id])
        response = await get_ai_response(
            user_id=user_id,
            context=context,
            history=history,
            message=message.text or "",
        )
    except Exception as exc:
        logger.exception("ai_chat_handler failed for user {}: {}", user_id, exc)
        await message.answer("Сервис ИИ временно недоступен. Попробуйте позже.")
        return

    CHAT_HISTORY[user_id].append({"role": "user", "content": message.text or ""})
    CHAT_HISTORY[user_id].append({"role": "assistant", "content": response})
    await message.answer(response)
