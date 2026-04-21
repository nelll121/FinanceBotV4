"""Handlers package."""

from aiogram import Router

from .admin import router as admin_router
from .ai_advisor import router as ai_advisor_router
from .debts import router as debts_router
from .expenses import router as expenses_router
from .income import router as income_router
from .savings import router as savings_router
from .start import router as start_router
from .summary import router as summary_router


def setup_routers() -> Router:
    """Create root router with all feature routers attached."""
    root = Router(name="root")
    root.include_router(start_router)
    root.include_router(admin_router)
    root.include_router(expenses_router)
    root.include_router(income_router)
    root.include_router(debts_router)
    root.include_router(savings_router)
    root.include_router(summary_router)
    root.include_router(ai_advisor_router)
    return root
