"""Background scheduler for summaries and reminders."""

from __future__ import annotations

from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from bot.config import TIMEZONE
from bot.services.ai_service import generate_evening_summary, generate_morning_summary
from bot.services.sheets import SheetsService
from bot.services.users import get_all_users

scheduler = AsyncIOScheduler(timezone=TIMEZONE)


def setup_scheduler(bot) -> None:
    """Setup jobs for all users with notifications enabled."""
    users = get_all_users()
    for user_id, data in users.items():
        if data.get("notifications"):
            add_user_jobs(bot, user_id, data)

    if not scheduler.running:
        scheduler.start()


def add_user_jobs(bot, user_id: str, user_data: dict) -> None:
    morning = user_data.get("morning_time", "09:00")
    evening = user_data.get("evening_time", "21:00")

    h_m, m_m = [int(x) for x in morning.split(":")]
    h_e, m_e = [int(x) for x in evening.split(":")]

    scheduler.add_job(
        send_morning_summary,
        "cron",
        hour=h_m,
        minute=m_m,
        args=[bot, user_id],
        id=f"morning_{user_id}",
        replace_existing=True,
    )
    scheduler.add_job(
        send_evening_summary,
        "cron",
        hour=h_e,
        minute=m_e,
        args=[bot, user_id],
        id=f"evening_{user_id}",
        replace_existing=True,
    )
    scheduler.add_job(
        check_overdue_debts,
        "cron",
        day_of_week="mon",
        hour=9,
        minute=0,
        args=[bot, user_id],
        id=f"debts_{user_id}",
        replace_existing=True,
    )


async def send_morning_summary(bot, user_id: str) -> None:
    try:
        users = get_all_users()
        user = users.get(str(user_id))
        if not user or not user.get("sheets_id"):
            return

        service = SheetsService(str(user["sheets_id"]))
        context = service.get_full_context()
        text = await generate_morning_summary(user_id, context)
        await bot.send_message(chat_id=int(user_id), text=f"☀️ Утренняя сводка\n\n{text}")
    except Exception as exc:
        logger.exception("send_morning_summary failed for user {}: {}", user_id, exc)


async def send_evening_summary(bot, user_id: str) -> None:
    try:
        users = get_all_users()
        user = users.get(str(user_id))
        if not user or not user.get("sheets_id"):
            return

        service = SheetsService(str(user["sheets_id"]))
        context = service.get_full_context()
        text = await generate_evening_summary(user_id, context)
        await bot.send_message(chat_id=int(user_id), text=f"🌙 Вечерняя сводка\n\n{text}")
    except Exception as exc:
        logger.exception("send_evening_summary failed for user {}: {}", user_id, exc)


async def check_overdue_debts(bot, user_id: str) -> None:
    try:
        users = get_all_users()
        user = users.get(str(user_id))
        if not user or not user.get("sheets_id"):
            return

        service = SheetsService(str(user["sheets_id"]))
        debts = service.get_active_debts()
        today = datetime.now().date()

        overdue = []
        for debt in debts:
            ret = str(debt.get("return_date") or "").strip()
            if not ret:
                continue
            try:
                due = datetime.strptime(ret, "%d.%m.%Y").date()
            except ValueError:
                continue
            if due < today:
                overdue.append(debt)

        if not overdue:
            return

        lines = ["⚠️ Напоминание: есть просроченные долги:"]
        for debt in overdue:
            lines.append(
                f"• {debt['name']} | {debt['type']} | {debt['amount']:.2f} | до {debt['return_date']}"
            )

        await bot.send_message(chat_id=int(user_id), text="\n".join(lines))
    except Exception as exc:
        logger.exception("check_overdue_debts failed for user {}: {}", user_id, exc)
