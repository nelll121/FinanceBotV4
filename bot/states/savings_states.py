"""Savings FSM states."""
from aiogram.fsm.state import State, StatesGroup


class SavingsStates(StatesGroup):
    goal_name = State()
    goal_amount = State()
    topup_goal_name = State()
    topup_amount = State()
