"""Debt FSM states."""
from aiogram.fsm.state import State, StatesGroup


class DebtStates(StatesGroup):
    debt_type = State()
    name = State()
    description = State()
    amount = State()
    due_date = State()
    note = State()
    return_index = State()
    partial_index = State()
    partial_amount = State()
