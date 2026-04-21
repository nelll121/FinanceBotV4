"""Google Sheets service layer (gspread-based)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

import gspread
from google.oauth2.service_account import Credentials

from bot.config import GOOGLE_CREDENTIALS, SheetsConfig

ACTIVE_DEBT_STATUSES = {"Активен", "Частично"}
SAVINGS_SHEET = "🎯 Цели"


@dataclass(slots=True)
class ExpenseEntry:
    date: str
    description: str
    category: str
    amount: float
    note: str = ""


@dataclass(slots=True)
class IncomeEntry:
    date: str
    description: str
    category: str
    amount: float
    note: str = ""


class SheetsService:
    """Wrapper around user spreadsheet operations."""

    def __init__(self, spreadsheet_id: str) -> None:
        self.spreadsheet_id = spreadsheet_id
        self._client = self._build_client()

    @staticmethod
    def _build_client() -> gspread.Client:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=scopes)
        return gspread.authorize(creds)

    def _month_sheet_name(self, dt: datetime | None = None) -> str:
        now = dt or datetime.now()
        return SheetsConfig.MONTHS[now.month - 1]

    def _worksheet(self, title: str) -> gspread.Worksheet:
        book = self._client.open_by_key(self.spreadsheet_id)
        return book.worksheet(title)

    def _first_empty_row(
        self,
        ws: gspread.Worksheet,
        col: int,
        row_start: int,
        row_end: int,
    ) -> int | None:
        values = ws.get(f"{gspread.utils.rowcol_to_a1(row_start, col)}:{gspread.utils.rowcol_to_a1(row_end, col)}")
        for idx, row in enumerate(values, start=row_start):
            if not row or not str(row[0]).strip():
                return idx
        return None

    def get_expense_categories(self, month_name: str | None = None) -> list[str]:
        month = month_name or self._month_sheet_name()
        ws = self._worksheet(month)
        start = SheetsConfig.EXP_CAT_RANGE_START
        col = SheetsConfig.EXP_CAT_RANGE_COL
        rng = f"{gspread.utils.rowcol_to_a1(start, col)}:{gspread.utils.rowcol_to_a1(start + 50, col)}"
        values = ws.get(rng)
        return [row[0].strip() for row in values if row and row[0].strip()]

    def get_income_categories(self, month_name: str | None = None) -> list[str]:
        month = month_name or self._month_sheet_name()
        ws = self._worksheet(month)
        start = SheetsConfig.INC_CAT_RANGE_START
        col = SheetsConfig.INC_CAT_RANGE_COL
        rng = f"{gspread.utils.rowcol_to_a1(start, col)}:{gspread.utils.rowcol_to_a1(start + 50, col)}"
        values = ws.get(rng)
        return [row[0].strip() for row in values if row and row[0].strip()]

    def append_expense(self, entry: ExpenseEntry, month_name: str | None = None) -> int:
        month = month_name or self._month_sheet_name()
        ws = self._worksheet(month)
        row = self._first_empty_row(
            ws,
            col=SheetsConfig.EXP_DATE_COL,
            row_start=SheetsConfig.EXP_DAILY_START,
            row_end=SheetsConfig.EXP_DAILY_END,
        )
        if row is None:
            raise RuntimeError("Не найдено свободной строки для расходов")

        updates = [
            (row, SheetsConfig.EXP_DATE_COL, entry.date),
            (row, SheetsConfig.EXP_DESC_COL, entry.description),
            (row, SheetsConfig.EXP_CAT_COL, entry.category),
            (row, SheetsConfig.EXP_AMT_COL, entry.amount),
            (row, SheetsConfig.EXP_NOTE_COL, entry.note),
        ]
        for r, c, value in updates:
            ws.update_cell(r, c, value)
        return row

    def append_income(self, entry: IncomeEntry, month_name: str | None = None) -> int:
        month = month_name or self._month_sheet_name()
        ws = self._worksheet(month)
        row = self._first_empty_row(
            ws,
            col=SheetsConfig.INC_DATE_COL,
            row_start=SheetsConfig.INC_DAILY_START,
            row_end=SheetsConfig.INC_DAILY_END,
        )
        if row is None:
            raise RuntimeError("Не найдено свободной строки для доходов")

        updates = [
            (row, SheetsConfig.INC_DATE_COL, entry.date),
            (row, SheetsConfig.INC_DESC_COL, entry.description),
            (row, SheetsConfig.INC_CAT_COL, entry.category),
            (row, SheetsConfig.INC_AMT_COL, entry.amount),
            (row, SheetsConfig.INC_NOTE_COL, entry.note),
        ]
        for r, c, value in updates:
            ws.update_cell(r, c, value)
        return row

    def add_debt(
        self,
        debt_type: str,
        name: str,
        amount: float,
        description: str = "",
        return_date: str | None = None,
        note: str = "",
    ) -> int:
        ws = self._worksheet(SheetsConfig.JOURNAL_SHEET)
        row = self._first_empty_row(
            ws,
            col=SheetsConfig.J_TYPE_COL,
            row_start=SheetsConfig.J_START_ROW,
            row_end=SheetsConfig.J_END_ROW,
        )
        if row is None:
            raise RuntimeError("Журнал долгов переполнен")

        today = datetime.now().strftime("%d.%m.%Y")
        ws.update_cell(row, SheetsConfig.J_TYPE_COL, debt_type)
        ws.update_cell(row, SheetsConfig.J_NAME_COL, name)
        ws.update_cell(row, SheetsConfig.J_DESC_COL, description)
        ws.update_cell(row, SheetsConfig.J_AMOUNT_COL, amount)
        ws.update_cell(row, SheetsConfig.J_REC_COL, today)
        ws.update_cell(row, SheetsConfig.J_RET_COL, return_date or "")
        ws.update_cell(row, SheetsConfig.J_STATUS_COL, "Активен")
        ws.update_cell(row, SheetsConfig.J_NOTE_COL, note)

        if debt_type == "Мне должны":
            self.append_expense(
                ExpenseEntry(
                    date=today,
                    description=f"Выдан займ: {name}",
                    category="Займ",
                    amount=amount,
                    note=description,
                )
            )
        elif debt_type == "Я должен":
            self.append_income(
                IncomeEntry(
                    date=today,
                    description=f"Получен займ: {name}",
                    category="Займ",
                    amount=amount,
                    note=description,
                )
            )
        return row

    def get_active_debts(self) -> list[dict]:
        ws = self._worksheet(SheetsConfig.JOURNAL_SHEET)
        rng = (
            f"{gspread.utils.rowcol_to_a1(SheetsConfig.J_START_ROW, SheetsConfig.J_TYPE_COL)}:"
            f"{gspread.utils.rowcol_to_a1(SheetsConfig.J_END_ROW, SheetsConfig.J_NOTE_COL)}"
        )
        rows = ws.get(rng)

        result: list[dict] = []
        for idx, row in enumerate(rows):
            row_values = row + [""] * (8 - len(row))
            debt_type, name, desc, amount, rec_date, ret_date, status, note = row_values[:8]
            status_value = str(status).strip() or "Активен"
            if not debt_type or status_value not in ACTIVE_DEBT_STATUSES:
                continue

            real_row = SheetsConfig.J_START_ROW + idx
            result.append(
                {
                    "index": len(result),
                    "row": real_row,
                    "type": str(debt_type),
                    "name": str(name),
                    "desc": str(desc),
                    "amount": float(str(amount).replace(" ", "") or 0),
                    "record_date": str(rec_date),
                    "return_date": str(ret_date),
                    "status": status_value,
                    "note": str(note),
                }
            )
        return result

    def return_debt_full(self, debt_index: int) -> dict:
        active = self.get_active_debts()
        if debt_index < 0 or debt_index >= len(active):
            raise IndexError("Debt index is out of range")

        debt = active[debt_index]
        ws = self._worksheet(SheetsConfig.JOURNAL_SHEET)
        row = debt["row"]
        amount = float(debt["amount"])
        today = datetime.now().strftime("%d.%m.%Y")

        ws.update_cell(row, SheetsConfig.J_STATUS_COL, "Возвращён")
        ws.update_cell(row, SheetsConfig.J_NOTE_COL, f"Полный возврат: {today}")

        if debt["type"] == "Мне должны":
            self.append_income(
                IncomeEntry(
                    date=today,
                    description=f"Возврат долга: {debt['name']}",
                    category="Займ",
                    amount=amount,
                    note=debt["desc"],
                )
            )
        else:
            self.append_expense(
                ExpenseEntry(
                    date=today,
                    description=f"Возврат долга: {debt['name']}",
                    category="Займ",
                    amount=amount,
                    note=debt["desc"],
                )
            )

        self.write_return_history(
            name=debt["name"],
            debt_type=debt["type"],
            paid=amount,
            remain=0,
            original=amount,
            return_type="Полный",
            desc=debt["desc"],
            record_date=debt["record_date"],
        )
        return debt

    def write_return_history(
        self,
        name: str,
        debt_type: str,
        paid: float,
        remain: float,
        original: float,
        return_type: str,
        desc: str = "",
        record_date: str = "",
    ) -> None:
        ws = self._worksheet(SheetsConfig.HISTORY_SHEET)
        row = self._first_empty_row(ws, col=1, row_start=2, row_end=500)
        if row is None:
            row = 500

        date_val = datetime.now().strftime("%d.%m.%Y")
        ws.update_cell(row, 1, date_val)
        ws.update_cell(row, 2, name)
        ws.update_cell(row, 3, desc)
        ws.update_cell(row, 4, debt_type)
        ws.update_cell(row, 5, return_type)
        ws.update_cell(row, 6, original)
        ws.update_cell(row, 7, paid)
        ws.update_cell(row, 8, remain)
        ws.update_cell(row, 9, record_date)

    def return_debt_partial(self, debt_index: int, paid: float) -> dict:
        active = self.get_active_debts()
        if debt_index < 0 or debt_index >= len(active):
            raise IndexError("Debt index is out of range")

        debt = active[debt_index]
        original = float(debt["amount"])
        if paid <= 0 or paid >= original:
            raise ValueError("Некорректная сумма частичного возврата")

        remain = round(original - paid, 2)
        today = datetime.now().strftime("%d.%m.%Y")

        ws = self._worksheet(SheetsConfig.JOURNAL_SHEET)
        row = debt["row"]
        ws.update_cell(row, SheetsConfig.J_AMOUNT_COL, remain)
        ws.update_cell(row, SheetsConfig.J_STATUS_COL, "Частично")
        ws.update_cell(row, SheetsConfig.J_NOTE_COL, f"Частичный возврат {paid} от {today}")

        if debt["type"] == "Мне должны":
            self.append_income(
                IncomeEntry(
                    date=today,
                    description=f"Частичный возврат долга: {debt['name']}",
                    category="Займ",
                    amount=paid,
                    note=debt["desc"],
                )
            )
        else:
            self.append_expense(
                ExpenseEntry(
                    date=today,
                    description=f"Частичный возврат долга: {debt['name']}",
                    category="Займ",
                    amount=paid,
                    note=debt["desc"],
                )
            )

        self.write_return_history(
            name=debt["name"],
            debt_type=debt["type"],
            paid=paid,
            remain=remain,
            original=original,
            return_type="Частичный",
            desc=debt["desc"],
            record_date=debt["record_date"],
        )

        updated = dict(debt)
        updated["amount"] = remain
        updated["status"] = "Частично"
        return updated

    def get_return_history(self, name: str | None = None) -> list[dict]:
        ws = self._worksheet(SheetsConfig.HISTORY_SHEET)
        rows = ws.get("A2:I500")
        result: list[dict] = []
        for row in rows:
            if not row:
                continue
            values = row + [""] * (9 - len(row))
            item = {
                "return_date": values[0],
                "name": values[1],
                "desc": values[2],
                "type": values[3],
                "return_type": values[4],
                "original": values[5],
                "paid": values[6],
                "remain": values[7],
                "record_date": values[8],
            }
            if name and str(item["name"]).strip().lower() != name.strip().lower():
                continue
            result.append(item)
        return result

    def get_ai_preferences(self) -> dict[str, str]:
        ws = self._worksheet(SheetsConfig.SETTINGS_SHEET)
        rows = ws.get("A3:B20")
        prefs: dict[str, str] = {}
        for row in rows:
            if len(row) < 2:
                continue
            key = str(row[0]).strip()
            val = str(row[1]).strip()
            if key:
                prefs[key] = val
        return prefs

    def save_ai_preference(self, key: str, value: str) -> bool:
        ws = self._worksheet(SheetsConfig.SETTINGS_SHEET)
        rows = ws.get("A3:A20")
        for idx, row in enumerate(rows, start=3):
            k = row[0].strip() if row else ""
            if k == key:
                ws.update_cell(idx, 2, value)
                return True
            if not k:
                ws.update_cell(idx, 1, key)
                ws.update_cell(idx, 2, value)
                return True
        return False

    def clear_ai_preferences(self) -> bool:
        ws = self._worksheet(SheetsConfig.SETTINGS_SHEET)
        ws.batch_clear(["A3:B20"])
        return True

    def get_day_operations(self, date: str) -> dict:
        """Return day operations by date in YYYY-MM-DD format."""
        dt = datetime.strptime(date, "%Y-%m-%d")
        month = self._month_sheet_name(dt)
        ws = self._worksheet(month)

        target = dt.strftime("%d.%m.%Y")

        expense_range = (
            f"{gspread.utils.rowcol_to_a1(SheetsConfig.EXP_DAILY_START, SheetsConfig.EXP_DATE_COL)}:"
            f"{gspread.utils.rowcol_to_a1(SheetsConfig.EXP_DAILY_END, SheetsConfig.EXP_NOTE_COL)}"
        )
        income_range = (
            f"{gspread.utils.rowcol_to_a1(SheetsConfig.INC_DAILY_START, SheetsConfig.INC_DATE_COL)}:"
            f"{gspread.utils.rowcol_to_a1(SheetsConfig.INC_DAILY_END, SheetsConfig.INC_NOTE_COL)}"
        )

        expenses_raw = ws.get(expense_range)
        income_raw = ws.get(income_range)

        expenses: list[dict] = []
        incomes: list[dict] = []

        for row in expenses_raw:
            row = row + [""] * (11 - len(row))
            r_date, desc, cat, amount, note = row[0], row[1], row[6], row[9], row[10]
            if str(r_date).strip() != target:
                continue
            amt = float(str(amount).replace(" ", "").replace(",", ".") or 0)
            expenses.append({"category": str(cat), "amount": amt, "desc": str(desc), "note": str(note)})

        for row in income_raw:
            row = row + [""] * (11 - len(row))
            r_date, desc, cat, amount, note = row[0], row[1], row[6], row[9], row[10]
            if str(r_date).strip() != target:
                continue
            amt = float(str(amount).replace(" ", "").replace(",", ".") or 0)
            incomes.append({"category": str(cat), "amount": amt, "desc": str(desc), "note": str(note)})

        return {
            "date": date,
            "expenses": expenses,
            "income": incomes,
            "total_expense": round(sum(x["amount"] for x in expenses), 2),
            "total_income": round(sum(x["amount"] for x in incomes), 2),
        }

    def get_full_context(self) -> dict:
        today = datetime.now().date()
        last_7_days = []
        for shift in range(7):
            day = today.fromordinal(today.toordinal() - shift)
            day_str = day.strftime("%Y-%m-%d")
            try:
                last_7_days.append(self.get_day_operations(day_str))
            except Exception:
                continue

        return {
            "month_summary": self.get_month_summary(),
            "active_debts": self.get_active_debts(),
            "savings_goals": self.get_savings_goals(),
            "recent_returns": self.get_return_history()[-5:],
            "ai_preferences": self.get_ai_preferences(),
            "last_7_days": last_7_days,
        }

    def get_month_summary(self, month_name: str | None = None) -> dict[str, float | str]:
        month = month_name or self._month_sheet_name()
        ws = self._worksheet(month)

        income = ws.cell(SheetsConfig.INC_TOTAL_ROW, SheetsConfig.INC_FACT_COL).value or "0"
        expense = ws.cell(SheetsConfig.EXP_TOTAL_ROW, SheetsConfig.EXP_FACT_COL).value or "0"

        income_value = float(str(income).replace(" ", "").replace(",", ".") or 0)
        expense_value = float(str(expense).replace(" ", "").replace(",", ".") or 0)

        return {
            "month": month,
            "income": income_value,
            "expense": expense_value,
            "balance": income_value - expense_value,
        }

    def _get_or_create_savings_sheet(self) -> gspread.Worksheet:
        book = self._client.open_by_key(self.spreadsheet_id)
        try:
            return book.worksheet(SAVINGS_SHEET)
        except gspread.WorksheetNotFound:
            ws = book.add_worksheet(title=SAVINGS_SHEET, rows=200, cols=8)
            ws.update("A1:E1", [["Название", "Цель", "Накоплено", "%", "Создано"]])
            return ws

    def get_savings_goals(self) -> list[dict]:
        ws = self._get_or_create_savings_sheet()
        values = ws.get("A2:E200")

        goals: list[dict] = []
        for row in values:
            padded = row + [""] * (5 - len(row))
            name, target, current, percent, created = padded[:5]
            if not str(name).strip():
                continue
            goals.append(
                {
                    "name": str(name),
                    "target_amount": float(str(target).replace(" ", "") or 0),
                    "current_amount": float(str(current).replace(" ", "") or 0),
                    "percent": float(str(percent).replace("%", "").replace(" ", "") or 0),
                    "created_at": str(created),
                }
            )
        return goals

    def add_savings_goal(self, name: str, target_amount: float) -> int:
        ws = self._get_or_create_savings_sheet()
        row = self._first_empty_row(ws, col=1, row_start=2, row_end=200)
        if row is None:
            raise RuntimeError("Лист целей заполнен")

        created = datetime.now().strftime("%d.%m.%Y")
        ws.update_cell(row, 1, name)
        ws.update_cell(row, 2, target_amount)
        ws.update_cell(row, 3, 0)
        ws.update_cell(row, 4, 0)
        ws.update_cell(row, 5, created)
        return row

    def update_savings_goal(self, goal_name: str, add_amount: float) -> dict:
        ws = self._get_or_create_savings_sheet()
        values = ws.get("A2:E200")

        for idx, row in enumerate(values, start=2):
            if not row:
                continue
            name = str(row[0]).strip()
            if name != goal_name:
                continue

            target = float(str(row[1]).replace(" ", "") or 0) if len(row) > 1 else 0.0
            current = float(str(row[2]).replace(" ", "") or 0) if len(row) > 2 else 0.0
            new_current = current + add_amount
            percent = (new_current / target * 100) if target > 0 else 0

            ws.update_cell(idx, 3, new_current)
            ws.update_cell(idx, 4, round(percent, 2))

            today = datetime.now().strftime("%d.%m.%Y")
            self.append_expense(
                ExpenseEntry(
                    date=today,
                    description=f"Пополнение цели: {goal_name}",
                    category="Накопления",
                    amount=add_amount,
                    note="",
                )
            )

            return {
                "name": goal_name,
                "target_amount": target,
                "current_amount": new_current,
                "percent": round(percent, 2),
            }

        raise ValueError("Цель не найдена")


def normalize_categories(values: Sequence[str]) -> list[str]:
    """Normalize category list for keyboard output."""
    seen: set[str] = set()
    result: list[str] = []
    for raw in values:
        value = raw.strip()
        if not value:
            continue
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
