"""Google Drive helpers for spreadsheet provisioning."""

from __future__ import annotations

import asyncio

import gspread
from google.oauth2.service_account import Credentials

from bot.config import GOOGLE_CREDENTIALS, TEMPLATE_SHEET_ID

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _build_client() -> gspread.Client:
    creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=SCOPES)
    return gspread.authorize(creds)


def _create_from_template_sync(user_email: str) -> str:
    if not TEMPLATE_SHEET_ID:
        raise RuntimeError("TEMPLATE_SHEET_ID is not configured")

    client = _build_client()
    title = f"FinanceBot_{user_email.split('@')[0]}"
    new_sheet = client.copy(TEMPLATE_SHEET_ID, title=title, copy_permissions=False)
    spreadsheet_id = new_sheet["id"]

    spreadsheet = client.open_by_key(spreadsheet_id)
    spreadsheet.share(user_email, perm_type="user", role="writer", notify=True)
    return spreadsheet_id


async def create_from_template(user_email: str) -> str:
    """Create user spreadsheet from template and share it with user email."""
    return await asyncio.to_thread(_create_from_template_sync, user_email)
