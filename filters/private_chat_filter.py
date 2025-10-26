from aiogram.filters.base import Filter
from aiogram  import types

class IsPrivateChat(Filter):
    async def __call__(self, message: types.Message):
        # if message.chat.type == "private":
        #     return True
        # return False
        return message.chat.type == "private"