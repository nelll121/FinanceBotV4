"""Configuration module for FinanceBot v2."""

from __future__ import annotations

import json
import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TEMPLATE_SHEET_ID = os.getenv("TEMPLATE_SHEET_ID")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Almaty")

GOOGLE_CREDENTIALS = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON", "{}"))


class SheetsConfig:
    """Google Sheets coordinates and static constants."""

    # Журнал долгов
    JOURNAL_SHEET = "📋 Журнал долгов"
    J_TYPE_COL = 3  # C
    J_NAME_COL = 4  # D
    J_DESC_COL = 5  # E
    J_AMOUNT_COL = 6  # F
    J_REC_COL = 7  # G
    J_RET_COL = 8  # H
    J_STATUS_COL = 9  # I
    J_NOTE_COL = 10  # J
    J_START_ROW = 6
    J_END_ROW = 55

    # Ежедневные расходы
    EXP_DATE_COL = 2  # B
    EXP_DESC_COL = 3  # C
    EXP_CAT_COL = 8  # H
    EXP_AMT_COL = 11  # K
    EXP_NOTE_COL = 12  # L
    EXP_DAILY_START = 34
    EXP_DAILY_END = 94

    # Ежедневные доходы
    INC_DATE_COL = 14  # N
    INC_DESC_COL = 15  # O
    INC_CAT_COL = 20  # T
    INC_AMT_COL = 23  # W
    INC_NOTE_COL = 24  # X
    INC_DAILY_START = 34
    INC_DAILY_END = 94

    # Итого для сводки месяца
    INC_TOTAL_ROW = 13
    INC_FACT_COL = 16  # P
    EXP_TOTAL_ROW = 22
    EXP_FACT_COL = 20  # T

    # Категории
    EXP_CAT_RANGE_START = 6
    EXP_CAT_RANGE_COL = 18  # R
    INC_CAT_RANGE_START = 6
    INC_CAT_RANGE_COL = 14  # N

    # История возвратов
    HISTORY_SHEET = "📜 История возвратов"

    # Настройки ИИ
    SETTINGS_SHEET = "⚙️ Настройки"

    MONTHS = [
        "Январь",
        "Февраль",
        "Март",
        "Апрель",
        "Май",
        "Июнь",
        "Июль",
        "Август",
        "Сентябрь",
        "Октябрь",
        "Ноябрь",
        "Декабрь",
    ]
