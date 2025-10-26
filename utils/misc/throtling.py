import asyncio
from aiogram.types import Message

# oddiy throttling misoli
user_timers = {}

async def throttle(message: Message, limit: int = 3):
    user_id = message.from_user.id
    if user_id in user_timers and (asyncio.get_event_loop().time() - user_timers[user_id]) < limit:
        await message.answer("⏳ Juda tez-tez yozayapsiz, biroz kuting.")
        return False
    user_timers[user_id] = asyncio.get_event_loop().time()
    return True
