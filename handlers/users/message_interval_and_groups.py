from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

import base64

from telethon.tl.types import InputPhoto

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import Channel, Chat
from telethon.errors import RPCError, FloodWaitError, ChatAdminRequiredError

import os
import asyncio
from dotenv import load_dotenv
from loader import bot
import json

from states.message_state import MessageState
from data.db.users.user import get_user, user_login_status
from data.db.messages.message_set import free_user_message_set

load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
ARCHIVE_CHANNEL_ID = os.getenv("ARCHIVE_CHANNEL_ID")
BOT_USERNAME = os.getenv("BOT_USERNAME")


router = Router()


# =========================================
# Faqat yangi guruhlarni olish (teskari filtr)
# =========================================
async def filter_new_groups(client: TelegramClient, old_group_ids: list[int]):
    """Avvalgi saqlangan ID larni tekshiradi va faqat yangi guruhlarni qaytaradi"""
    new_groups = []
    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        if isinstance(entity, (Channel, Chat)):
            if getattr(entity, "megagroup", False) or entity.__class__.__name__ == "Chat":
                if entity.id not in old_group_ids:
                    perms = getattr(entity, "default_banned_rights", None)
                    if perms and getattr(perms, "send_messages", False):
                        continue
                    new_groups.append((entity.id, entity.title))
    return new_groups


# =========================================
# Asosiy guruhlarni olish handler
# =========================================
@router.callback_query(StateFilter(MessageState.message_interval), F.data.startswith("message_interval,"))
async def message_interval(call: CallbackQuery, state: FSMContext):
    interval = int(call.data.split(",")[1])
    await state.update_data(message_interval=interval)
    await call.message.edit_text("⏳ Guruhlaringiz olinmoqda, iltimos kuting...")

    user_groups = []
    client = None

    try:
        user_data = await get_user(
            telegram_id=call.from_user.id,
            username=call.from_user.username,
            name=call.from_user.full_name
        )

        if not user_data or not user_data.get("userSession"):
            await call.message.edit_text("❌ Sessiya topilmadi.")
            return

        try: 
            client = TelegramClient(StringSession(user_data.get("userSession")), api_id=API_ID, api_hash=API_HASH)
        except Exception as e:
            print("(message_interval_and_groups) Userni akkauntiga ulanishda hatolik: ", e)
            await state.clear()
            await user_login_status(call.from_user.id)
            return

        await client.start()
        await state.update_data(stringSession=user_data.get("userSession"))

        # Avval saqlangan eski guruhlar ro‘yxatini olish
        old_groups = []

        # 🔁 faqat yangi guruhlarni olish
        groups = await filter_new_groups(client, old_groups)

        async def test_group(group):
            group_id, title = group
            try:
                msg = await client.send_message(group_id, "✅ test")
                await client.delete_messages(group_id, msg.id)
                return (group_id, title, False)
            except (FloodWaitError, ChatAdminRequiredError, RPCError):
                return None
            except Exception as e:
                print(f"[{title}] testda xato: {e}")
                return None

        sem = asyncio.Semaphore(30)  # parallel ishlar soni
        async def limited(group):
            async with sem:
                return await test_group(group)

        results = await asyncio.gather(*[limited(g) for g in groups])
        user_groups = [r for r in results if r]

    except Exception as e:
        print("❌ Guruhlarni olishda xatolik:", e)
        await call.message.edit_text("⚠️ Guruhlarni olishda xatolik yuz berdi.")
        await state.clear()
    finally:
        if client:
            await client.disconnect()

    if not user_groups:
        await call.message.edit_text("❌ Yangi guruhlar topilmadi.")
        return

    await state.update_data(all_groups=user_groups, page=0)
    per_page = 10
    keyboard = all_groups_button(user_groups, 0, len(user_groups), per_page)

    await call.message.edit_text(
        f"📨 Yangi guruhlar ro‘yxati:\n"
        f"🔹 Jami: {len(user_groups)} ta\n"
        f"Ko‘rsatilmoqda: 1–{min(per_page, len(user_groups))}",
        reply_markup=keyboard
    )

# =========================================
# Guruh tanlash
# =========================================
@router.callback_query(F.data.startswith("groups_"))
async def toggle_group_selection(call: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        all_groups = data.get("all_groups", [])
        page = data.get("page", 0)
        per_page = 10
        changed = False  # faqat real o‘zgarish bo‘lsa True bo‘ladi

        if call.data == "groups_select_all":
            changed = False
            for i, g in enumerate(all_groups):
                if not g[2]:  # faqat belgilanmaganlarni belgilaymiz
                    all_groups[i] = (g[0], g[1], True)
                    changed = True

        elif call.data == "groups_unselect_all":
            changed = False
            for i, g in enumerate(all_groups):
                if g[2]:  # faqat belgilanganni o‘chiramiz
                    all_groups[i] = (g[0], g[1], False)
                    changed = True

        elif call.data.startswith("groups_select_"):
            group_id = int(call.data.split("_")[2])
            for i, g in enumerate(all_groups):
                if g[0] == group_id:
                    all_groups[i] = (g[0], g[1], not g[2])
                    changed = True
                    break

        elif call.data.startswith("groups_page_"):
            new_page = int(call.data.split("_")[-1])
            max_page = (len(all_groups) - 1) // per_page
            if 0 <= new_page <= max_page and new_page != page:
                page = new_page
                changed = True

        if changed:
            await state.update_data(all_groups=all_groups, page=page)
            keyboard = all_groups_button(all_groups, page, len(all_groups), per_page)
            start_idx = page * per_page
            end_idx = min(start_idx + per_page, len(all_groups))

            await call.message.edit_text(
                f"📨 Guruhlar tanlovi\n\n"
                f"Jami: {len(all_groups)} ta\n"
                f"Sahifa: {start_idx+1}–{end_idx}",
                reply_markup=keyboard
            )

            result = [g[0] for g in all_groups if g[2]]
            await state.update_data(result=result)
        else:
            await call.answer("⚠️ Hech qanday o‘zgarish bo‘lmadi.")

    except Exception as e:
        print(f"❌ Guruh tanlashda xato: {e}")
        await call.answer("Xatolik yuz berdi!", show_alert=True)


# =========================================
# Saqlash
# =========================================
@router.callback_query(F.data == "save_groups")
async def save_groups_handler(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    result = data.get("result", [])
    if not result:
        await call.message.edit_text("⚠️ Hech qanday guruh tanlanmadi.")
        return

    try:
        # Agar rasm yuborilgan bo'lsa, uni kanalda saqlaymiz va meta JSON ni tayyorlaymiz
        meta_json = None
        photo_id = None
        access_hash = None
        file_reference = None
        saved = None
        message_id = None
        if data.get("image_status") and data.get("msg_id"):
            
            try:
                client = TelegramClient(StringSession(data["stringSession"]), api_id=API_ID, api_hash=API_HASH)
                await client.start()
                await client.get_dialogs()

                bot_entity = await client.get_entity(BOT_USERNAME)
                all_messages = []
                async for message in client.iter_messages(bot_entity, limit=100):
                    all_messages.append(message)
                
                for i in range(len(all_messages)):
                    if all_messages[i].text != "/free_message":
                        if all_messages[i].text == "Rasmingiz qabul qilindi ✅":
                            message_id = all_messages[i+1].id
                            break
                    else:
                        break
                fresh_msg = await client.get_messages(8282931306, ids=message_id)
                p = fresh_msg.photo
                photo_id = p.id
                access_hash = p.access_hash
                file_reference = p.file_reference
                # iphoto = InputPhoto(id=p.id, access_hash=p.access_hash, file_reference=p.file_reference)
                # await client.send_file(-1003011042874, iphoto, caption="Test habar")
                # print(f"\n\nrefrence {p.id}\n\n")

                # Bot API uchun kanal chat_id -100 bilan boshlanadi
                saved = await bot.copy_message(
                    chat_id=ARCHIVE_CHANNEL_ID,
                    from_chat_id=call.from_user.id,
                    message_id=int(data["msg_id"]),
                    caption=f"{call.from_user.id}",
                    disable_notification=True
                )
                print(f"\n\nsaved: {saved.message_id}\n\n")

            except Exception as e:
                print("Userni akkauntiga ulanib rasmni refrence ni olishda hatolik: ", e)

        # Ma'lumotlarni DB va Redisga yozamiz
        await free_user_message_set(
            string_session=data["stringSession"],
            telegram_id=call.from_user.id,
            user_message=data["message"],
            message_interval=data["message_interval"],
            user_groups=result,
            file_reference= base64.b64encode(file_reference).decode("ascii") if file_reference else None,
            photo_id=photo_id if photo_id else None,
            access_hash=access_hash if access_hash else None,
            channel_photo_id=saved.message_id if message_id else None
        )

        await call.message.edit_text(f"✅ {len(result)} ta guruh saqlandi.")
    except Exception as e:
        print("❌ Saqlashda xato:", e)
        await call.message.edit_text("⚠️ Saqlashda xatolik yuz berdi.")
    finally:
        await state.clear()


# =========================================
# Bekor qilish
# =========================================
@router.callback_query(F.data == "cancel_groups")
async def cancel_groups_handler(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("❌ Amaliyot bekor qilindi.")
    await state.clear()


# =========================================
# Inline keyboard yaratish
# =========================================
def all_groups_button(all_groups, page: int, total: int, per_page: int):
    start = page * per_page
    end = min(start + per_page, total)
    groups_page = all_groups[start:end]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    # Guruh tugmalari
    row = []
    for i, group in enumerate(groups_page, start=1):
        row.append(InlineKeyboardButton(
            text=f"{'✅' if group[2] else '❌'} {group[1]}",
            callback_data=f"groups_select_{group[0]}"
        ))
        if i % 2 == 0:
            keyboard.inline_keyboard.append(row)
            row = []
    if row:
        keyboard.inline_keyboard.append(row)

    # Navigatsiya
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"groups_page_{page-1}"))
    if end < total:
        nav.append(InlineKeyboardButton(text="➡️ Oldinga", callback_data=f"groups_page_{page+1}"))
    if nav:
        keyboard.inline_keyboard.append(nav)

    # Boshqaruv tugmalari
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="✅ Barchasini belgilash", callback_data="groups_select_all"),
        InlineKeyboardButton(text="❌ Barchasini o‘chirish", callback_data="groups_unselect_all"),
    ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="Saqlash ♻️", callback_data="save_groups"),
        InlineKeyboardButton(text="Bekor qilish 🔴", callback_data="cancel_groups"),
    ])
    return keyboard
