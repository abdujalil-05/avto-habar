from aiogram.filters.base import Filter
from aiogram.types import Message


class IsGroup(Filter):
    async def __call__(self, message: Message):
        return message.chat.type == "group" or message.chat.type == "supergroup"