from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from datetime import datetime
from decimal import Decimal
import json

from data.db.users.user import get_user

from keyboards.inline.user_sign_in_button import login_inline_button
from keyboards.inline.free_message_inline_button import free_message_menu, free_select
from keyboards.inline.message_interval import message_interval
from states.message_state import MessageState
from filters.admin_filter import IsAdmin
from data.db.messages.message_set import delete_free_message

router = Router()


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


@router.message(Command("free_message"))
async def free_message_handler(message: Message):
    message_user = message.from_user
    user = await get_user(telegram_id=message_user.id, username=message_user.username, name=message_user.full_name)
    admin = await IsAdmin()(message)
    if user:
        print("\n\nusers", user)
        if not user.get("user_status"):
            await message.answer("👮🏻‍♀️ Bepul habar yuborish uchun ro'yhatdan o'tishingiz kerak\n\n", reply_markup=login_inline_button)
        elif admin:
            await message.answer("Siz bepul habar yuborishni tanladingiz ✅\n\nHabar turini tanlang:", reply_markup=free_message_menu)
        elif user.get("messages_id"):
            print("user message: ", user.get("messages_id"))
            await message.answer("Yangi habar kiritish uchun eski habaringizni o'chirishingiz kerak", reply_markup=free_select)
        elif not user.get("free_message") and user.get("user_status"):  
            await message.answer("Siz bepul habar yuborishni tanladingiz ✅\n\nHabar turini tanlang:", reply_markup=free_message_menu)
        elif _to_datetime(user.get("free_message")) > datetime.now():
            await message.answer("Siz bepul habar yuborishni tanladingiz ✅\n\nHabar turini tanlang:", reply_markup=free_message_menu)
        else:
            await message.answer(f"❌ Siz oldin bepul habar yuborishdan foydalangansiz!\n\n")
            
    else:
        await message.answer("👮🏻‍♀️ Bepul habar yuborish uchun ro'yhatdan o'tishingiz kerak\n\n", reply_markup=login_inline_button)


@router.callback_query(F.data == "free_delete_message")
async def free_message_delete_handler(call: CallbackQuery):
    await delete_free_message(call.from_user.id)
    await call.message.edit_text("Habaringiz muvaffaqiyatli o'chirildi ✅")
    await call.message.answer("\n\nHabar turini tanlang:", reply_markup=free_message_menu)


@router.callback_query(F.data == "free_cancel")
async def free_message_cancel_handler(call: CallbackQuery):
    await call.message.edit_text("Amaliyot bekor qilindi ❌")
    


@router.callback_query(F.data == "free_message_photo")
async def free_message_photo_handler(call: CallbackQuery, state: FSMContext):
    user = call.from_user
    user = await get_user(telegram_id=user.id, username=user.username, name=user.full_name)
    admin = await IsAdmin()(call)
    if user.get("messages_id"):
        if not admin:
            await call.answer("Siz eski tugmani bosdingiz ❗️", show_alert=True)
            return
    await call.message.edit_text("Avto habar uchun rasmni yuboring 🌆")
    await state.set_state(MessageState.image_message)




@router.message(MessageState.image_message)
async def free_message_photo_get_handler(message: Message, state: FSMContext):
    try:
        if message.photo:
            await message.answer("Rasmingiz qabul qilindi ✅")
            await state.update_data(image_status=True)
            await state.update_data(message_photo_file_id=message.photo[-1].file_id, msg_id=message.message_id)
            await state.set_state(MessageState.message)
            await message.answer("📜 Habar matnini kiriting: ")

            # await message.answer
        else:
            await message.answer("Siz hato rasm yubordingiz❌ Iltimos tekshirib qaytadan yuboring")

    except Exception as e:
        print("User tekin habarda habar kiritish jarayonida hato: ", e)



@router.callback_query(F.data == "free_message_standart")
async def free_message_standart_handler(call: CallbackQuery, state: FSMContext):
    user = call.from_user
    user = await get_user(telegram_id=user.id, username=user.username, name=user.full_name)
    admin = await IsAdmin()(call.message)
    if user.get("messages_id"):
        if not admin:
            await call.answer("Siz eski tugmani bosdingiz ❗️", show_alert=True)
            return
    await call.message.edit_text("📜 Habar matnini kiriting: ")
    await state.update_data(message_status=False, image_status=False)
    await state.set_state(MessageState.message)



@router.message(MessageState.message)
async def free_message_standart_message_handler(message: Message, state: FSMContext):
    try:
        if message.text:
            await message.answer("Habaringiz qabul qilindi ✅")
            await state.update_data(message=message.text)
            await message.answer("⏱️ Qancha vaqt oralig'ida guruhlarga habar yuborilsin", reply_markup=message_interval)
            await state.set_state(MessageState.message_interval)
        else:
            await message.answer("Siz hato habar yubordingiz❌ Iltimos tekshirib qaytadan yuboring")
    except Exception as e:
        print("User tekin habarda habar kiritish jarayonida hato: ", e)