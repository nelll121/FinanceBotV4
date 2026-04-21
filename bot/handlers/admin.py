"""Admin-only command handlers."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import ADMIN_USER_ID
from bot.services.users import (
    count_users,
    get_all_users,
    get_user,
    grant_ai_access,
    revoke_ai_access,
)

router = Router(name="admin")


def _is_admin(user_id: int) -> bool:
    return ADMIN_USER_ID and str(user_id) == str(ADMIN_USER_ID)


@router.message(Command("users"))
async def list_users(message: Message) -> None:
    if not message.from_user or not _is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа.")
        return

    users = get_all_users()
    if not users:
        await message.answer("Пользователей пока нет.")
        return

    lines = [f"👥 Всего пользователей: {count_users()}\n"]
    for uid, payload in users.items():
        ai = "✅" if payload.get("ai_access") else "❌"
        sheet = "✅" if payload.get("sheets_id") else "❌"
        lines.append(
            f"ID: {uid} | {payload.get('name', '?')} | "
            f"AI: {ai} | Sheet: {sheet}"
        )
    await message.answer("\n".join(lines))


@router.message(Command("grant"))
async def grant_access(message: Message) -> None:
    if not message.from_user or not _is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа.")
        return

    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Использование: /grant <user_id>")
        return

    target_id = int(parts[1])
    if not get_user(target_id):
        await message.answer(f"Пользователь {target_id} не найден.")
        return

    grant_ai_access(target_id)
    await message.answer(f"✅ Доступ к ИИ выдан пользователю {target_id}.")

    try:
        await message.bot.send_message(
            chat_id=target_id,
            text="✅ Вам выдан доступ к ИИ советнику!"
        )
    except Exception:
        pass


@router.message(Command("revoke"))
async def revoke_access(message: Message) -> None:
    if not message.from_user or not _is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа.")
        return

    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Использование: /revoke <user_id>")
        return

    target_id = int(parts[1])
    if not get_user(target_id):
        await message.answer(f"Пользователь {target_id} не найден.")
        return

    revoke_ai_access(target_id)
    await message.answer(f"✅ Доступ к ИИ отозван у пользователя {target_id}.")

    try:
        await message.bot.send_message(
            chat_id=target_id,
            text="❌ Доступ к ИИ советнику отозван.\n"
                 "Добавьте свой Anthropic API ключ: /setkey sk-ant-..."
        )
    except Exception:
        pass


@router.message(Command("broadcast"))
async def broadcast(message: Message) -> None:
    if not message.from_user or not _is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа.")
        return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /broadcast <текст>")
        return

    text = parts[1]
    users = get_all_users()
    sent = 0
    for uid in users:
        try:
            await message.bot.send_message(chat_id=int(uid), text=text)
            sent += 1
        except Exception:
            pass

    await message.answer(f"✅ Отправлено {sent}/{len(users)} пользователям.")
