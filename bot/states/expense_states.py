"""Expense FSM states."""
from aiogram.fsm.state import State, StatesGroup


class ExpenseStates(StatesGroup):
    category = State()
    amount = State()
    description = State()
    note = State()
