"""Formatting helpers."""

from __future__ import annotations

from datetime import datetime


def fmt_money(value: float | int) -> str:
    """Format number as money: 10000 → '10 000 ₸'."""
    return f"{value:,.0f}".replace(",", " ") + " ₸"


def fmt_date(dt: datetime | None = None) -> str:
    """Format datetime to DD.MM.YYYY."""
    return (dt or datetime.now()).strftime("%d.%m.%Y")


def parse_date(value: str) -> str:
    """Parse DD.MM.YYYY → YYYY-MM-DD for Sheets."""
    dt = datetime.strptime(value.strip(), "%d.%m.%Y")
    return dt.strftime("%Y-%m-%d")


def parse_iso_date(iso_str: str) -> str:
    """Parse ISO date from Google Sheets → DD.MM.YYYY.
    
    Handles: '2026-04-19T00:00:00.000Z', '2026-04-19', datetime objects.
    Always use this for dates coming from Google Sheets.
    """
    if not iso_str:
        return ""
    raw = str(iso_str).split("T")[0].strip()
    try:
        dt = datetime.strptime(raw, "%Y-%m-%d")
        return dt.strftime("%d.%m.%Y")
    except ValueError:
        return raw


def progress_bar(current: float, target: float, width: int = 10) -> str:
    """Generate progress bar: progress_bar(40, 100) → '████░░░░░░ 40%'."""
    if target <= 0:
        return "░" * width + " 0%"
    pct = min(current / target, 1.0)
    filled = int(pct * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"{bar} {pct * 100:.0f}%"
