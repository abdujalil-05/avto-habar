from aiogram.fsm.state import State, StatesGroup


class UserBalanceState(StatesGroup):
    summa = State()
    check_photo = State()
    check = State()