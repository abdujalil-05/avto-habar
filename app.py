import asyncio
from loader import bot, dp

from data.db.free_message_time.create_free_message_time_db import create_free_message_time_db
from data.db.users.create_user_db import create_user_db
from data.db.messages.create_message_db import create_message_db
from data.db.connection.connection import init_db_pool, init_redis
from data.db.admin.create_admin_db import create_admin_db

from utils.notify_admins import on_startup_notify
from utils.get_users import get_user_db
from handlers.users import users as users_router
from handlers.admins import admins as admins_router
# from handlers.messages import messages as messages_router


async def main():
    await bot.delete_webhook(drop_pending_updates=True)  # eski update’larni tozalash

    await init_redis()
    await init_db_pool()
    
    
    await create_free_message_time_db()
    await create_user_db()
    await create_message_db()
    await create_admin_db()

    dp.include_router(users_router)
    dp.include_router(admins_router)
    # dp.include_router(messages_router)

    # Adminlarga xabar berish

    await get_user_db()

    # Polling
    await on_startup_notify(bot)
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())



