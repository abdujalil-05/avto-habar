from aiogram.fsm.state import State, StatesGroup


class MessageState(StatesGroup):
    image_message = State()
    message = State()
    message_interval = State()
    user_groups = State()