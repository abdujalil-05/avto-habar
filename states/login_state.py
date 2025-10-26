from aiogram.fsm.state import State, StatesGroup


class UserLogin(StatesGroup):
    phone_number = State()
    code = State()
    two_step_password = State()