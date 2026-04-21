"""CRUD service for local users storage (`data/users.json`)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from threading import Lock
from typing import Any

DATA_DIR = Path("data")
USERS_PATH = DATA_DIR / "users.json"

_storage_lock = Lock()


@dataclass(slots=True)
class UserRecord:
    """In-memory representation of a registered bot user."""

    user_id: int
    name: str
    sheets_id: str | None = None
    api_key: str | None = None
    ai_access: bool = False
    timezone: str = "Asia/Almaty"
    morning_time: str = "09:00"
    evening_time: str = "21:00"
    notifications: bool = True
    registered_at: str = field(default_factory=lambda: date.today().isoformat())
    is_admin: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "sheets_id": self.sheets_id,
            "api_key": self.api_key,
            "ai_access": self.ai_access,
            "timezone": self.timezone,
            "morning_time": self.morning_time,
            "evening_time": self.evening_time,
            "notifications": self.notifications,
            "registered_at": self.registered_at,
            "is_admin": self.is_admin,
        }


def _ensure_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not USERS_PATH.exists():
        USERS_PATH.write_text("{}\n", encoding="utf-8")


def _read() -> dict[str, dict[str, Any]]:
    _ensure_storage()
    raw = USERS_PATH.read_text(encoding="utf-8").strip()
    if not raw:
        return {}
    return json.loads(raw)


def _write(data: dict[str, dict[str, Any]]) -> None:
    _ensure_storage()
    USERS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _uid(user_id: int | str) -> str:
    return str(user_id)


def get_all_users() -> dict[str, dict[str, Any]]:
    """Return all saved users as a dictionary keyed by Telegram user id."""
    with _storage_lock:
        return _read()


def get_user(user_id: int | str) -> dict[str, Any] | None:
    """Return a user payload by Telegram user id."""
    with _storage_lock:
        return _read().get(_uid(user_id))


def user_exists(user_id: int | str) -> bool:
    with _storage_lock:
        return _uid(user_id) in _read()


def is_registered(user_id: int | str) -> bool:
    """User exists and has linked spreadsheet id."""
    with _storage_lock:
        user = _read().get(_uid(user_id))
        return bool(user and user.get("sheets_id"))


def is_admin(user_id: int | str) -> bool:
    with _storage_lock:
        user = _read().get(_uid(user_id))
        return bool(user and user.get("is_admin"))


def get_api_key(user_id: int | str) -> str | None:
    """Resolve AI key for user according to ai_access + api_key semantics.

    Returns:
        - user api_key if set
        - empty string if ai_access enabled but custom key not set (caller should use ENV admin key)
        - None if AI access disabled
    """
    with _storage_lock:
        user = _read().get(_uid(user_id))
        if not user:
            return None
        custom = user.get("api_key")
        if custom:
            return str(custom)
        if user.get("ai_access"):
            return ""
        return None


def save_user(record: UserRecord) -> dict[str, dict[str, Any]]:
    """Insert or replace user record and persist storage."""
    with _storage_lock:
        users = _read()
        users[_uid(record.user_id)] = record.to_dict()
        _write(users)
        return users


def update_user(user_id: int | str, **fields: Any) -> dict[str, Any] | None:
    """Patch one or many fields for an existing user record."""
    with _storage_lock:
        users = _read()
        key = _uid(user_id)
        if key not in users:
            return None
        users[key].update(fields)
        _write(users)
        return users[key]


def grant_ai_access(user_id: int | str) -> dict[str, Any] | None:
    return update_user(user_id, ai_access=True, api_key=None)


def revoke_ai_access(user_id: int | str) -> dict[str, Any] | None:
    return update_user(user_id, ai_access=False)


def set_user_api_key(user_id: int | str, key: str) -> dict[str, Any] | None:
    return update_user(user_id, api_key=key.strip(), ai_access=True)


def delete_user(user_id: int | str) -> bool:
    """Delete user from storage. Returns True if user existed."""
    with _storage_lock:
        users = _read()
        removed = users.pop(_uid(user_id), None)
        if removed is None:
            return False
        _write(users)
        return True


def count_users() -> int:
    """Return number of registered users."""
    with _storage_lock:
        return len(_read())
