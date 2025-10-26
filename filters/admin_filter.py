from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram.enums import ChatMemberStatus

from data.db.admin.admin import getAdmin, get_redis, get_pool

class IsAdminGroup(BaseFilter):
    def __init__(self, bot):
        self.bot = bot

    async def __call__(self, message: Message) -> bool:
        # Faqat guruh va supergroup xabarlarida ishlaydi
        if message.chat.type not in ["group", "supergroup"]:
            return False

        # ChatMember ma'lumotlarini olish
        chat_member = await self.bot.get_chat_member(
            chat_id=message.chat.id,
            user_id=message.from_user.id
        )
        
        # Admin yoki owner bo'lsa True, aks holda False
        return chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        # if message.chat.type != "private":
        #     return False
        print("admin id", message.from_user.id)
        admin = await getAdmin(message.from_user.id)
        return admin