import json
from datetime import datetime, timedelta
from ..connection.connection import get_pool, get_redis
from decimal import Decimal



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

async def free_user_message_set(
    string_session,
    telegram_id,
    user_message,
    message_interval,
    user_groups,
    photo_id,
    access_hash,
    channel_photo_id,
    file_reference: str = None,
):
    r = await get_redis()
    pool = await get_pool()

    free_time = await r.get("free_time")
    free_time = int(free_time) if free_time else 240

    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                now = datetime.now()
                end_time = now + timedelta(minutes=free_time)
                end_reference_time = now + timedelta(days=7)

                # user_groups ni JSON formatda saqlaymiz
                user_groups_json = json.dumps(user_groups)

                # Xabar qo'shish
                await cursor.execute("""
                    INSERT INTO messages
                        (message, message_interval, file_reference, groups_id, user_id, end_time, session, message_status, photo_id, access_hash, last_reference_time, end_reference_time, channel_photo_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (user_message, message_interval, file_reference, user_groups_json, telegram_id, end_time, string_session, True, photo_id, access_hash, now, end_reference_time.isoformat(), channel_photo_id))
                await conn.commit()

                last_id = cursor.lastrowid

                # Redis-ga saqlash
                await cursor.execute(
                    "SELECT * FROM messages WHERE user_id = %s",
                    (telegram_id,)
                )
                new_message = await cursor.fetchone()
                if new_message:
                    new_message = serialize_user(new_message)
                    await r.set(f"message:{telegram_id}", json.dumps(new_message))
                    # await
                    print("\n\nredisga saqlandi\n\n")

                # User paket vaqtlarini yangilash
                await cursor.execute("""
                    UPDATE users
                    SET paket_start_time = %s, paket_end_time = %s, messages_id = %s, free_message = %s
                    WHERE telegram_id = %s
                """, (now, end_time, f"[{last_id}]", end_time, telegram_id))
                await conn.commit()

                # Redis-ga user-ni saqlash
                await cursor.execute(
                    "SELECT * FROM users WHERE telegram_id = %s",
                    (telegram_id,)
                )
                user = await cursor.fetchone()
                if user:
                    user = serialize_user(user)
                    await r.set(f"{telegram_id}", json.dumps(user))

            except Exception as e:
                print("Userni habarini sozlashda hatolik:", e)



async def delete_free_message(user_id):
    r = await get_redis()
    pool = await get_pool()

    try:
        await r.delete(str(user_id))
        await r.delete(f"message:{user_id}")
    except Exception as e:
        print("Redisdan user yoki message kalitini o'chirishda xatolik: ", e)

    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                await cursor.execute(
                    "DELETE FROM messages WHERE user_id = %s",
                    (user_id,)
                )
                await cursor.execute(
                    "UPDATE users SET messages_id = %s", (None,)
                )
                await conn.commit()
                if cursor.rowcount > 0:
                        return True
                else:
                    return False
            except Exception as e:
                print("❌ MySQL da user yoki xabarlarni o‘chirishda xatolik:", e)