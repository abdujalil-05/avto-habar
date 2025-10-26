import asyncio
import json
import os
import time
import random
from datetime import datetime, timedelta
from decimal import Decimal
from aiogram import Bot

import base64

from telethon.tl.types import InputPhoto

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors.rpcerrorlist import FileReferenceExpiredError
from dotenv import load_dotenv

from data.db.connection.connection import get_pool,  get_redis  # sizniki bilan mos
from data.db.users.user import user_login_status

load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")



load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ARCHIVE_CHANNEL_ID = os.getenv("ARCHIVE_CHANNEL_ID")
BOT_USERNAME = os.getenv("BOT_USERNAME")



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


def normalize_message_data(val):
    """Redisdan o‘qilgan JSON qiymatni tozalab, dict qilib qaytaradi."""
    msg = json.loads(val)

    # 1️⃣ Agar list bo‘lsa, dict shaklga o‘tkazamiz
    if isinstance(msg, list):
        try:
            return {
                "id": msg[0],
                "message": msg[1],
                "message_interval": msg[2],
                "file_reference": msg[3],
                "groups_id": msg[4],
                "user_id": msg[5],
                "end_time": msg[6],
                "message_status": msg[7],
                "session": msg[8],
                "last_message_time": msg[9],
                "channel_photo_id": msg[10],
                "last_reference_time": msg[11],
                "end_reference_time": msg[12],
                "photo_id": msg[13],
                "access_hash":msg[14],
            }
        except Exception as e:
            print("⚠️ Listni dict ga aylantirishda xatolik:", e)
            return None

    # 2️⃣ Agar dict bo‘lsa — o‘sha holicha qaytaramiz
    elif isinstance(msg, dict):
        return msg

    else:
        print("⚠️ Noma’lum message formati:", type(msg))
        return None




def _to_datetime(val):
    """String yoki datetime -> datetime. Agar None bo‘lsa None qaytaradi."""
    if not val:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, (int, float)):
        return datetime.fromtimestamp(val)
    try:
        return datetime.fromisoformat(val)
    except Exception:
        try:
            return datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None


async def process_message_key(msg: dict, r, key: str, bot: Bot):
    try:
        user_id = msg.get("user_id")
        session_str = msg.get("session")
        message_text = msg.get("message")
        message_status = msg.get("message_status")
        message_photo_file_id = msg.get("message_photo_file_id")
        groups_field = msg.get("groups_id")
        message_interval = int(msg.get("message_interval", 0))
        end_time = _to_datetime(msg.get("end_time"))
        last_msg_time = _to_datetime(msg.get("last_message_time"))
        channel_photo_id = msg.get("channel_photo_id")
        end_reference_time = _to_datetime(msg.get("end_reference_time"))  # ✅
        # end_reference_time = _to_datetime("end_reference_time")
        photo_id = msg.get("photo_id")
        access_hash = msg.get("access_hash")
        file_reference = base64.b64decode(msg.get("file_reference")) if msg.get("file_reference") else None
        now = datetime.now()

        reference_check = False


        print(f"\n\nrefrence type: {type(file_reference)}\n\n")

        # ✅ End time check
        if end_time and now >= end_time:
            try:
                await r.delete(key)
                await bot.send_message(
                    chat_id=user_id,
                    text="Harid qilgan paketingiz muddati tugadi. Iltimos, paketni qayta faollashtiring ✅",
                )
            except Exception as e:
                print(f"[{key}] ❌ Paket tugaganda o‘chirish xatosi:", e)
            return
        
        # ✅ TelegramClient bilan ulanish
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
        await client.connect()

        if not await client.is_user_authorized():
            await client.disconnect()
            await r.delete(key)
            await bot.send_message(
                chat_id=user_id,
                text="❌ Akkount avtorizatsiya qilinmagan. Iltimos, qaytadan ro‘yxatdan o‘ting.",
            )
            return


        # reference tekshiruvi
        
        if end_reference_time and now >= end_reference_time:
            try:
                random_key = random.randint(10000000, 99999999)
                await bot.copy_message(chat_id=user_id, from_chat_id=ARCHIVE_CHANNEL_ID, message_id=channel_photo_id)
                await bot.send_message(chat_id=user_id, text=f"{random_key}")
                
                bot_entity = await client.get_entity(BOT_USERNAME)
                all_messages = []
                async for message in client.iter_messages(bot_entity, limit=100):
                        all_messages.append(message)
                    
                for i in range(len(all_messages)):
                    if all_messages[i].text == f"{random_key}":
                        message_id = all_messages[i+1].id
                        random_key_id = all_messages[i].id
                        print(f"\n\nmessage: {all_messages[i+1]}\n\nmessage id: {message_id}   | random_key : {random_key}.  random_key_id: {random_key_id}  \n")
                        break

                # fresh_msg = await client.get_messages(8282931306, ids=message_id)
                
                fresh_msg = await client.get_messages(bot_entity, ids=message_id)  # ✅ yuqorida get_entity qilgansiz

                
                p = fresh_msg.photo
                photo_id = p.id
                access_hash = p.access_hash
                file_reference = p.file_reference

                await client.delete_messages(bot_entity, [message_id, random_key_id], revoke=True)

                # await bot.delete_message(chat_id=user_id, message_id=random_key_id)
                # await bot.delete_message(chat_id=user_id, message_id=message_id)

                pool = await get_pool()

                async with pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        try:
                            now = datetime.now()
                            end_reference_time = now + timedelta(weeks=1)
                            await cursor.execute(
                                "UPDATE messages SET photo_id = %s, access_hash = %s, file_reference = %s, last_reference_time = %s, end_reference_time = %s  WHERE user_id = %s",
                                (photo_id, access_hash, base64.b64encode(file_reference).decode("ascii"), now, end_reference_time, user_id)
                            )
                            last_id = cursor.lastrowid

                            await cursor.execute(
                                "SELECT * FROM messages WHERE id = %s", (user_id,)
                            )

                            new_message = await cursor.fetchone()
                            if new_message:
                                await r.delete(key)
                                new_message = serialize_user(new_message)
                                await r.set(f"message:{user_id}", json.dumps(new_message))
                            reference_check = True
                        except Exception as e:
                            print("Userni reference ni yangilab mysql va redisga yozishda hatolik: ", e)
            except Exception as e:
                print("Userni reference ni yangilashda hatolik: ", e)
                


        # ✅ Interval tekshiruvi
        if last_msg_time and (now - last_msg_time).total_seconds() < (message_interval-1) * 60:
            return

        # ✅ Session tekshiruvi
        if not session_str:
            await r.delete(key)
            await bot.send_message(
                chat_id=user_id,
                text="❌ Sessiya topilmadi. Iltimos, qaytadan ro‘yxatdan o‘ting.",
            )
            await user_login_status(user_id)
            pool = await get_pool()
            async with pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute(
                            "UPDATE users SET user_status = %s, phone_number = %s, userSession = %s WHERE telegram_id = %s",
                            (False, None, None, user_id)
                        )
            return

        # ✅ Guruhlar parsing
        try:
            groups = json.loads(groups_field)
            if not isinstance(groups, list):
                raise ValueError("groups_id JSON emas")
        except Exception:
            groups = [int(x.strip()) for x in str(groups_field).split(",") if x.strip().isdigit()]

        if not groups:
            print(f"[{key}] 🚫 Hech qanday guruh topilmadi.")
            return

        if not message_status:
            print(f"{key} o'chirildi")
            await r.delete(key)
            return


       
        await client.get_dialogs()

        delay = 1.0 if len(groups) <= 50 else 0.8
        avto_caption = message_text + "\n\n📨 Ushbu habar @AvtoHabarYubor_bot orqali yuborildi"

        for group in groups:
            group = int(group)
            if file_reference:
                try:
                    iphoto = InputPhoto(id=photo_id, access_hash=access_hash, file_reference=file_reference)
                    await client.send_file(group, iphoto, caption=message_text)
                except Exception as e:
                    await client.send_message(group, message_text)
                    print("guruhga habar yuborishda hatolik: ", e)
            else:
                await client.send_message(group, message_text)
            await asyncio.sleep(delay)
        
        # ✅ Oxirgi yuborilgan vaqtni yangilash
        if reference_check:
            msg["last_message_time"] = datetime.now().isoformat()
            msg["last_reference_time"] = datetime.now().isoformat()
            # msg["end_reference_time"] = end_reference_time
            msg["end_reference_time"] = end_reference_time.isoformat() if end_reference_time else None  # ✅
            msg["file_reference"] = base64.b64encode(file_reference).decode("ascii")
            msg["access_hash"] = access_hash
            msg["photo_id"] = photo_id
        else:
            msg["last_message_time"] = datetime.now().isoformat()
        await r.set(key, json.dumps(msg, ensure_ascii=False))

    except Exception as e:
        print(f"[{key}] ❌ process_message_key xatosi:", e)

    finally:
        try:
            if "client" in locals():
                await client.disconnect()
        except Exception as e:
            print(f"[{key}] ❌ Disconnect xatosi:", e)


CHECK_INTERVAL = 60  # sekund


async def send_messages_main(bot: Bot):
    """Redisdan message:* kalitlarini olib, real-time interval bilan xabarlarni qayta ishlaydi."""
    last_check = 0

    while True:
        try:
            now = time.time()
            # CHECK_INTERVAL soniya o‘tgach tekshiradi
            if now - last_check >= CHECK_INTERVAL:
                last_check = now
                r = await get_redis()
                print("🔁 send_messages_main ishga tushdi")

                keys = await r.keys("message:*")  # ✅ Yangi kalitlar har safar to‘liq olinadi
                print(f"🔑 Topilgan kalitlar: {keys}")
                print(keys)

                if not keys:
                    print("📭 Yangi xabarlar topilmadi...")
                else:
                    tasks = []
                    for key in keys:
                        val = await r.get(key)
                        if not val:
                            continue
                        try:
                            msg = normalize_message_data(val=val)
                            if not msg:
                                print(f"⚠️ {key} uchun ma’lumotni o‘qib bo‘lmadi")
                                continue
                            tasks.append(asyncio.create_task(process_message_key(msg, r, key, bot)))
                        except Exception as e:
                            print(f"⚠️ JSON xatosi ({key}): {e}")

                    if tasks:
                        await asyncio.gather(*tasks)

            # Har yarim soniyada minimal kutish, CPUni 100% band qilmaslik uchun
            await asyncio.sleep(0.5)

        except Exception as e:
            print(f"❌ send_messages_main loop xatosi: {e}")
            await asyncio.sleep(5)
def _to_bot_channel_id(val) -> int:
    """Bot API uchun kanal chat_id: -100 prefiksini kafolatlaydi.
    meta["channel_id"] ijobiy bo'lsa -> -100{val} ga aylantiradi.
    """
    try:
        s = str(int(val))
    except Exception:
        s = str(val)
    if s.startswith("-100"):
        return int(s)
    if s.startswith("-"):
        # allaqachon manfiy, lekin -100 emas — shundayligicha qoldiramiz
        return int(s)
    return int(f"-100{s}")
