from data.db.connection.connection import get_pool, get_redis
import json

from datetime import datetime
from decimal import Decimal




def user_tuple_to_dict(user_tuple):
    columns = [
        "id", "telegram_id", "username", "phone_number", "name",
        "status", "free_message", "user_start_bot", "paket_start_time",
        "paket_end_time", "user_balance", "messages_id", "channel_group_date_time",
        "channel_count", "group_count", "user_status", "userSession", "user_groups"
    ]

    user_dict = dict(zip(columns, user_tuple))

    # datetime va Decimal turlarni stringga o‘zgartirish
    for k, v in user_dict.items():
        if isinstance(v, datetime):
            user_dict[k] = v.isoformat()  # masalan: "2025-10-25T19:46:42"
        elif isinstance(v, Decimal):
            user_dict[k] = float(v)  # yoki str(v)
        elif isinstance(v, bytes):
            user_dict[k] = v.decode()  # ba'zan Redis yoki MySQL bytes qaytaradi

    return user_dict





async def getAdmin(admin_id):
    r = await get_redis()
    val = await r.get(f"admin:{admin_id}")
    admin = json.loads(val) if val else None
    if admin:
        print("admin:", admin)
        return True
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                await cursor.execute(
                    "SELECT * FROM admins WHERE user_id = %s", (admin_id,)
                )    
                admin = await cursor.fetchone()
                if admin:
                    await r.set(f"admin:{admin_id}", json.dumps(admin))
                    return
                return False
            except Exception as e:
                print("get Adminda hatolik: ", e)


async def admin_delete_user(user_id):
    r = await get_redis()
    # Redisdan user va unga bog'liq message keyini ham o'chiramiz
    try:
        await r.delete(str(user_id))
        await r.delete(f"message:{user_id}")
    except Exception as e:
        print("Redisdan user yoki message kalitini o'chirishda xatolik: ", e)

    pool = await get_pool()

    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                # Avval messages jadvalidan userga tegishli yozuvlarni o'chiramiz
                await cursor.execute(
                    "DELETE FROM messages WHERE user_id = %s", (user_id,)
                )
                # So'ng users jadvalidan userni o'chiramiz
                await cursor.execute(
                    "DELETE FROM users WHERE telegram_id = %s", (user_id,)
                )
                await conn.commit()
                if cursor.rowcount > 0:
                    return True
                else:
                    return False
            except Exception as e:
                print("❌ Admin orqali MySQL da user yoki xabarlarni o‘chirishda xatolik:", e)



async def admin_user_add_balance_db(user_id, balance):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "UPDATE users SET user_balance = %s WHERE telegram_id = %s",
                (balance, user_id)
            )
            await conn.commit()
            await cursor.execute(
                "SELECT * FROM users WHERE telegram_id = %s", (user_id,)
            )
            user = await cursor.fetchone()
            if user:
                r = await get_redis()
                user = user_tuple_to_dict(user)
                await r.set(f"{user_id}", json.dumps(user))
                val = await r.get(f"{user_id}")
                user = user_tuple_to_dict(val) if val else None
                if user:
                    return user
            else:
                return None