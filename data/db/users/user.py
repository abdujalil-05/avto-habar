from ..connection.connection import get_pool, get_redis
import json
import ast
from datetime import datetime, timedelta
from decimal import Decimal


def _parse_channels(channels_str):
    """channels ustunini string -> list aylantiradi"""
    if not channels_str:
        return []
    try:
        return json.loads(channels_str)
    except Exception:
        try:
            return ast.literal_eval(channels_str)
        except Exception:
            return []
        

def serialize_user(user_tuple):
    new_tuple = []
    for item in user_tuple:
        if isinstance(item, (datetime, Decimal)):
            if isinstance(item, datetime):
                new_tuple.append(item.isoformat())
            else:  # Decimal
                new_tuple.append(str(item))
        else:
            new_tuple.append(item)
    return tuple(new_tuple)


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




async def add_user(telegram_id, username, name):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                # Faqat telegram_id unique bo‘lishi kerak, shuning uchun
                await cursor.execute("""
                    INSERT INTO users (telegram_id, username, name, user_status)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE username=%s, name=%s
                """, (telegram_id, username, name,False,  username, name))
                await conn.commit()

                # Bazadan qayta o‘qib olish
                user = await get_user(telegram_id, username, name)
                if user:
                    r = await get_redis()
                    if isinstance(user, dict):
                        await r.set(str(telegram_id), json.dumps(user))
                        return user
                    else:
                        user = user_tuple_to_dict(user) if user else None
                        return user
                    # user = user_tuple_to_dict(user)
                    await r.set(str(telegram_id), json.dumps(user))
                return False

            except Exception as e:
                print("User qo‘shishda xatolik:", e)
                return False
            



async def get_user(telegram_id, username, name):
    r = await get_redis()
    val = await r.get(str(telegram_id))
    user = None
    if val:
        val = json.loads(val)
        if isinstance(val, dict):
            return val
        else:
            user = user_tuple_to_dict(val) if val else None
    if user and user.get("username") == username and user.get("name") == name:
        return user 
    

    # DB'dan olish
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                await cursor.execute(
                    "SELECT * FROM users WHERE telegram_id = %s", (telegram_id,)
                )
                user = await cursor.fetchone()
                if user:
                    # username yoki name o‘zgargan bo‘lsa yangilaymiz
                    if user[2] == username or user[4]:
                        await cursor.execute(
                            "UPDATE users SET username = %s, name = %s WHERE telegram_id = %s",
                            (username, name, telegram_id)
                        )
                        await conn.commit()
                        await cursor.execute(
                            "SELECT * FROM users WHERE telegram_id = %s", (telegram_id,)
                        )
                        user = await cursor.fetchone()
                        if user:
                            r = await get_redis()
                            if isinstance(user, dict):
                                await r.set(str(telegram_id), json.dumps(user))
                                return user
                            else:
                                user = user_tuple_to_dict(user) if user else None
                            # user = user_tuple_to_dict(user)
                            await r.set(str(telegram_id), json.dumps(user))

                    else:
                        user = user_tuple_to_dict(user_tuple=user)
                        await r.set(str(telegram_id), json.dumps(user), ex=4*3600)
                return user
            except Exception as e:
                print("DB dan user olishda xatolik:", e)
                return None
            



async def get_user_by_id(telegram_id):
    r = await get_redis()

    val = await r.get(str(telegram_id))
    user = None
    if val:
        val = json.loads(val)
        if isinstance(val, dict):
            return val
        else:
            user = user_tuple_to_dict(val) if val else None
            return user

    
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                await cursor.execute(
                    "SELECT * FROM users WHERE telegram_id = %s", (telegram_id,)
                )
                user = await cursor.fetchone()
                if user:
                    r = await get_redis()
                    if isinstance(user, dict):
                        await r.set(str(telegram_id), json.dumps(user))
                        return user
                    else:
                        user = user_tuple_to_dict(user) if user else None
                        await r.set(str(telegram_id), json.dumps(user))
                        return user
            except Exception as e:
                print("Id orqali user olishda hatolik: ", e)
                return None



async def user_login_db(telegram_id, phone, string_session):
    r = await get_redis()
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                await cursor.execute(
                    "UPDATE users SET phone_number = %s, user_status = %s, userSession = %s WHERE telegram_id = %s", (phone, True, string_session, telegram_id)
                )
                await conn.commit()
                await cursor.execute(
                    "SELECT * FROM users WHERE telegram_id = %s", (telegram_id,)
                )
                user = await cursor.fetchone()
                if user:
                    r = await get_redis()
                    if isinstance(user, dict):
                        await r.set(str(telegram_id), json.dumps(user))
                        return user
                    else:
                        user = user_tuple_to_dict(user) if user else None
                        await r.set(str(telegram_id), json.dumps(user))
                return True
            
            except Exception as e:
                print("User login qilishda hatolik: ", e)
                return False


async def user_phone_number_check(phone):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM users WHERE phone_number = %s", (phone,)
            )
            user = await cursor.fetchone()
            return user




async def free_user_message_set(telegram_id, user_message, message_interval, user_groups, message_photo_file_id: str = None):
    r = await get_redis()
    pool = await get_pool()
    free_time = await r.get("free_time") 
    free_time = int(free_time) or 240

    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            now = datetime.now()
            end_time = now + timedelta(minutes=free_time)
            user_groups = str(user_groups)
            await cursor.execute("""
                    INSERT INTO messages (message, message_interval, message_photo_file_id, groups_id, user_id, end_time)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (user_message, message_interval, message_photo_file_id,  user_groups, telegram_id, end_time))
            await conn.commit()
            last_id = cursor.lastrowid

            await cursor.execute(
                "UPDATE users SET paket_start_time = %s, paket_end_time = %s, messages_id = %s WHERE telegram_id = %s",
                (now, end_time, last_id, telegram_id)
            )



async def user_login_status(telegram_id):
    pool = await get_pool()

    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                await cursor.execute(
                    "UPDATE users SET user_status = %s, phone_number = %s, userSession = %s WHERE telegram_id = %s",
                    (False, None, None,  telegram_id)
                )
                await conn.commit()
                await cursor.execute(
                    "SELECT * FROM users WHERE telegram_id = %s", (telegram_id,)
                )
                user = await cursor.fetchone()
                if user:
                    r = await get_redis()
                    user = serialize_user(user_tuple=user)
                    await r.set(str(telegram_id), json.dumps(user))

            except Exception as e:
                print("Userni statusini o'zgartirishda hatolik: ", e)

# import asyncio
# import redis.asyncio as redis
# import json

# # Global Redis pool
# _redis = None
# REDIS_URL = "redis://localhost"
# REDIS_MAX_CONNECTIONS = 200

# # -----------------------------
# # Redis init & get_pool
# # -----------------------------
# async def init_redis():
#     """Redis pool yaratish"""
#     global _redis
#     if _redis is None:
#         _redis = redis.Redis.from_url(
#             REDIS_URL,
#             decode_responses=True,
#             max_connections=REDIS_MAX_CONNECTIONS
#         )
#         # test
#         pong = await _redis.ping()
#         if pong:
#             print("✅ Redis ishlamoqda!")
#         else:
#             print("❌ Redis javob bermadi!")

# async def get_redis():
#     """Redis poolni olish"""
#     global _redis
#     if _redis is None:
#         await init_redis()
#     return _redis

# # -----------------------------
# # Misollar: tuple / hash / list
# # -----------------------------
# async def redis_examples():
#     r = await get_redis()

#     # -------- String + tuple JSON --------
#     t = (123, "hello", True)
#     await r.set("my_tuple", json.dumps(t))
#     val = await r.get("my_tuple")
#     tuple_val = tuple(json.loads(val))
#     print("Tuple:", tuple_val)

#     # -------- Hash --------
#     user_hash = {"username": "abdujalil", "status": "free", "balance": 100}
#     await r.hset("user:1", mapping=user_hash)
#     user_data = await r.hgetall("user:1")
#     print("Hash:", user_data)

#     # -------- List --------
#     my_list = (1, 2, 3, 4)
#     await r.rpush("my_list", *my_list)  # tuple unpacking
#     list_vals = await r.lrange("my_list", 0, -1)
#     print("List:", list_vals)

# # -----------------------------
# # Test run
# # -----------------------------
# if __name__ == "__main__":
#     asyncio.run(redis_examples())




# import asyncio
# import redis.asyncio as redis
# import json

# # Global Redis pool
# _redis = None
# REDIS_URL = "redis://localhost"
# REDIS_MAX_CONNECTIONS = 200

# # -----------------------------
# # Redis init & get_pool
# # -----------------------------
# async def init_redis():
#     """Redis pool yaratish"""
#     global _redis
#     if _redis is None:
#         _redis = redis.Redis.from_url(
#             REDIS_URL,
#             decode_responses=True,
#             max_connections=REDIS_MAX_CONNECTIONS
#         )
#         pong = await _redis.ping()
#         if pong:
#             print("✅ Redis ishlamoqda!")
#         else:
#             print("❌ Redis javob bermadi!")

# async def get_redis():
#     """Redis poolni olish"""
#     global _redis
#     if _redis is None:
#         await init_redis()
#     return _redis

# # -----------------------------
# # Redis set & get misollari
# # -----------------------------
# async def redis_examples():
#     r = await get_redis()

#     # -------- String + tuple JSON --------
#     t = (123, "hello", True)
#     key_tuple = "my_tuple"
#     await r.set(key_tuple, json.dumps(t), ex=3600)  # TTL 1 soat

#     # Get qilish
#     val = await r.get(key_tuple)
#     tuple_val = tuple(json.loads(val)) if val else None
#     print("Tuple:", tuple_val)

#     # -------- Hash --------
#     user_hash = {"username": "abdujalil", "status": "free", "balance": 100}
#     key_hash = "user:1"
#     await r.hset(key_hash, mapping=user_hash)
#     # Get qilish
#     user_data = await r.hgetall(key_hash)
#     print("Hash:", user_data)

#     # -------- List --------
#     my_list = (1, 2, 3, 4)
#     key_list = "my_list"
#     await r.rpush(key_list, *my_list)  # tuple unpacking
#     # Get qilish
#     list_vals = await r.lrange(key_list, 0, -1)
#     print("List:", list_vals)

# # -----------------------------
# # Test run
# # -----------------------------
# if __name__ == "__main__":
#     asyncio.run(redis_examples())
