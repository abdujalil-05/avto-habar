from aiogram.fsm.state import State, StatesGroup


class AdminDeleteState(StatesGroup):
    user_id = State()


class AdminUserAddBalance(StatesGroup):
    user_id = State()
    summa = State()
    check = State()