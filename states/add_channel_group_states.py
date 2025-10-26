from aiogram.fsm.state import State, StatesGroup


class addPrivateChannel(StatesGroup):
    channel_link_check = State()
    channel_link = State()