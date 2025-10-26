from data.db.connection.connection import get_pool, get_redis
import json
import aiomysql
from datetime import datetime, date
from decimal import Decimal


def serialize_user(user):
    """datetime va Decimal turlarni JSON uchun mos formatga o‘giradi"""
    new_user = {}
    for k, v in user.items():
        if isinstance(v, (datetime, date)):
            new_user[k] = v.isoformat()
        elif isinstance(v, Decimal):
            new_user[k] = str(v)
        else:
            new_user[k] = v
    return new_user



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


async def get_user_db():
    """
    Dastur ishga tushganda MySQL'dan userlarni olib,
    Redis RAM xotirasiga vaqtinchalik yuklaydi.
    Dastur o‘chsa, ma’lumotlar ham avtomatik o‘chadi.
    """
    pool = await get_pool()
    redis = await get_redis()

    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            try:
                await cursor.execute("SELECT * FROM users")
                users = await cursor.fetchall()
                await cursor.execute("SELECT * FROM free_time WHERE id = 1")
                free_time = await cursor.fetchone()
                await cursor.execute("SELECT * FROM messages")
                all_messages = await cursor.fetchall()
                await cursor.execute("SELECT * FROM admins")
                admins = await cursor.fetchall()

                await redis.flushall()


                if not users:
                    print("❌ MySQLda user topilmadi.")
                    return
                if not free_time:
                    print("❌ Free time da vaqt topilmadi.")
                if not all_messages:
                    print("❌ Habarlar topilmadi.")


                pipe = redis.pipeline(transaction=False)
                for user in users:
                    u = serialize_user(user)

                    # TTL qo‘ymaslik – faqat RAM'da saqlanadi
                    pipe.set(f"{u.get('telegram_id')}", json.dumps(u))
                # print(all_messages)
                for message in all_messages:
                    m = serialize_user(message)
                    pipe.set(f"message:{message['user_id']}", json.dumps(m))
                
                for admin in admins:
                    pipe.set(f"admin:{admin['user_id']}", json.dumps(admin))

                pipe.set("free_time", f"{free_time['time']}")
                

                await pipe.execute()
                print(f"✅ {len(users)} ta user Redis RAM xotirasiga yuklandi (faqat vaqtinchalik).")
                print(f"{free_time} belgilandi ✅")
                print(f"{len(all_messages)} ta message Redis RAM xotirasiga yuklandi ✅")
                print(f"{len(admins)} ta admin Redis RAM xotirasiga yuklandi ✅")
            except Exception as e:
                print("⚠️ Mysqldan Redisga userlarni olishda xatolik:", e)
