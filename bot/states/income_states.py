"""Income FSM states."""
from aiogram.fsm.state import State, StatesGroup


class IncomeStates(StatesGroup):
    category = State()
    amount = State()
    description = State()
    note = State()
