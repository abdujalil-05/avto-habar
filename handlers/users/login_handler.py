from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from states.login_state import UserLogin
from keyboards.default.cancel_button import cancel_button
from data.db.users.user import user_login_db, user_phone_number_check

from telethon import TelegramClient, errors
from telethon.sessions import StringSession

import os
import re
from dotenv import load_dotenv

load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

# +998XXYYYYYYY format
# uzbek_phone_regex = re.compile(r'^\+998\d{9}$')
uzbek_phone_regex = re.compile(r'^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$')

router = Router()


@router.message(StateFilter(UserLogin), F.text == "❌ Bekor qilish")
async def sign_out_cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Ro'yhatdan o'tish bekor qilindi ✅", reply_markup=ReplyKeyboardRemove())

@router.callback_query(F.data == "login")
async def user_sign_in_handler(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer(
        "Misol uchun +998901234567\nChet el raqamiga ham ochsangiz bo'ladi🤩\n\n📲 Iltimos telefon raqamingizni yuboring:", reply_markup=cancel_button
    )
    await state.set_state(UserLogin.phone_number)

@router.message(UserLogin.phone_number)
async def user_sign_in_phone_number_handler(message: Message, state: FSMContext):
    if not uzbek_phone_regex.match(message.text):
        await message.answer("Siz hato raqam yubordingiz ❌ Iltimos tekshirib qaytadan yuboring❗️")
        return

    phone = message.text.strip()
    user = await user_phone_number_check(phone= phone)
    if user:
        await message.answer("Bu raqam oldin ro'yhatdan o'tgan ❌\n\nAgarda bu raqamga kira olmayotgan bo'lsangiz adminga murojat qiling❗️\n👮🏻‍♀️ Admin: @bosh_director")
        return
    
    # Yangi client yaratish
    await message.answer("📨 kod yuborilmoqda...")
    client = TelegramClient(StringSession(), api_id=API_ID, api_hash=API_HASH)
    await client.connect()

    try:
        # Telefon raqamiga kod yuborish va phone_code_hash olish
        sent_code = await client.send_code_request(phone)
        await state.update_data(phone=phone, client=client, phone_code_hash=sent_code.phone_code_hash)
        await message.answer("❗️ Kodni X.X.X.X.X ko'rinishida kiriting.\n\nX larni o'rniga kodni yozing. \nMisol uchun: 1.2.3.4.5\n\n📩 Sizning telefon raqamingizga kod yuborildi, iltimos kodni yuboring:")
        await state.set_state(UserLogin.code)
    except Exception as e:
        await message.answer("Sign-in paytida xato yuz berdi. Iltimos qayta urinib ko'ring.")
        print("Sign-in error:", e)
        await client.disconnect()




@router.message(UserLogin.code)
async def user_sign_in_code_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    client: TelegramClient = data["client"]
    phone: str = data["phone"]
    phone_code_hash: str = data.get("phone_code_hash")
    code = message.text.strip()

    if not client or not phone:
        await message.answer("❌ Sessiya topilmadi, boshidan /start bosqichini boshlang.")
        await state.clear()
        return

    try:
        # Sign-in kod orqali phone_code_hash bilan
        await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
        await message.answer("✅ Siz muvaffaqiyatli tizimga kirdingiz!\n\nQaytadan /profile buyrug'ini yuboring")
        session_string = client.session.save()
        # print("String session 1: ", session_string)
        await state.update_data(stringSession=session_string)

        await user_login_db(telegram_id=message.from_user.id, phone=phone, string_session=session_string)
        await state.clear()
        await client.disconnect()

    except errors.SessionPasswordNeededError:
        await message.answer("🔒 Hisobingiz 2-bosqichli parol bilan himoyalangan. Iltimos, parolni kiriting:")
        session_string = client.session.save()
        # print("String session 1: ", session_string)
        await state.update_data(stringSession=session_string)
        await state.set_state(UserLogin.two_step_password)

    except errors.PhoneCodeExpiredError:
        await message.answer("❌ Kod muddati o'tgan yoki raqamlar orasiga \".\" qo'ymagansiz. Iltimos, yana boshlang.")
        await client.disconnect()
        await state.clear()

    except errors.PhoneCodeInvalidError:
        await message.answer("❌ Kod noto‘g‘ri. Iltimos, qaytadan yuboring.")

    except Exception as e:
        print("Code kiritishda xato:", e,"\n\n")
        await message.answer("❌ Noma'lum xato yuz berdi. Iltimos qaytadan urinib ko'ring.")
        await client.disconnect()
        await state.clear()




@router.message(UserLogin.two_step_password)
async def user_sign_in_two_step_password_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    client: TelegramClient = data['client']
    phone: str = data["phone"]
    password = message.text.strip()

    try:
        await client.sign_in(password=password)
        await message.answer("✅ Siz muvaffaqiyatli tizimga kirdingiz!\n\nQaytadan /start buyrug'ini yuboring")
        data = await state.get_data()
        print(data)
        session_string = data["stringSession"]

        
        await user_login_db(telegram_id=message.from_user.id, phone=phone, string_session=session_string)
        await state.clear()
        await client.disconnect()

    except errors.PasswordHashInvalidError:
        await message.answer("❌ Parol noto‘g‘ri. Iltimos, qayta kiriting.")

    except Exception as e:
        print("Ikki bosqichli parol kiritishda xato:", e)
        await message.answer("❌ Noma'lum xato yuz berdi.")
        await client.disconnect()
        await state.clear()



# from aiogram import Router, F
# from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
# from aiogram.fsm.context import FSMContext
# from aiogram.filters import StateFilter

# from states.login_state import UserLogin
# from keyboards.default.cancel_button import cancel_button
# from data.db.users.user import user_login_db

# from telethon import TelegramClient, errors
# from telethon.sessions import StringSession

# import os
# import re
# from dotenv import load_dotenv

# load_dotenv()
# API_ID = int(os.getenv("API_ID"))
# API_HASH = os.getenv("API_HASH")

# # +998XXYYYYYYY format
# uzbek_phone_regex = re.compile(r'^\+998\d{9}$')
# numbers = re.compile(r'^[0-9]+$')

# router = Router()


# # ===========================================================
# # 1️⃣ BEKOR QILISH HANDLER
# # ===========================================================
# @router.message(StateFilter(UserLogin), F.text == "❌ Bekor qilish")
# async def sign_out_cancel_handler(message: Message, state: FSMContext):
#     await state.clear()
#     await message.answer("Ro'yhatdan o'tish bekor qilindi ✅", reply_markup=ReplyKeyboardRemove())


# # ===========================================================
# # 2️⃣ LOGIN BOSHLASH CALLBACK
# # ===========================================================
# @router.callback_query(F.data == "login")
# async def user_sign_in_handler(call: CallbackQuery, state: FSMContext):
#     await call.message.delete()
#     await call.message.answer(
#         "Misol uchun +998901234567\n📲 Iltimos telefon raqamingizni yuboring:", reply_markup=cancel_button
#     )
#     await state.set_state(UserLogin.phone_number)


# # ===========================================================
# # 3️⃣ TELEFON RAQAMNI QABUL QILISH
# # ===========================================================
# @router.message(UserLogin.phone_number)
# async def user_sign_in_phone_number_handler(message: Message, state: FSMContext):
#     if not uzbek_phone_regex.match(message.text):
#         await message.answer("❌ Noto‘g‘ri raqam formati. Iltimos, +998XXXXXXXXX ko‘rinishida yuboring.")
#         return

#     phone = message.text.strip()

#     # Fayl o‘rniga string session
#     client = TelegramClient(StringSession(), api_id=API_ID, api_hash=API_HASH)
#     await client.connect()

#     try:
#         # Kod yuborish
#         sent_code = await client.send_code_request(phone)

#         # State ichiga ma’lumotlarni saqlaymiz
#         await state.update_data(
#             phone=phone,
#             client=client,
#             phone_code_hash=sent_code.phone_code_hash,
#         )

#         # await message.answer(
#         #     "📩 Kod yuborildi!\n\nIltimos, kodni shu shaklda kiriting: 1.2.3.4.5"
#         # )
#         await message.answer("❗️ Kodni X.X.X.X.X ko'rinishida kiriting.\n\nX larni o'rniga kodni yozing. \nMisol uchun: 1.2.3.4.5\n\n📩 Sizning telefon raqamingizga kod yuborildi, iltimos kodni yuboring:")

#         await state.set_state(UserLogin.code)

#     except Exception as e:
#         print("Sign-in error:", e)
#         await message.answer("❌ Kod yuborishda xato. Iltimos, qayta urinib ko‘ring.")
#         await client.disconnect()
#         await state.clear()


# # ===========================================================
# # 4️⃣ KODNI QABUL QILISH
# # ===========================================================
# @router.message(UserLogin.code)
# async def user_sign_in_code_handler(message: Message, state: FSMContext):
#     data = await state.get_data()
#     client: TelegramClient = data.get("client")
#     phone: str = data.get("phone")
#     phone_code_hash: str = data.get("phone_code_hash")
#     code = message.text.strip().replace(".", "")

#     if not client or not phone:
#         await message.answer("❌ Sessiya topilmadi, boshidan /start bosqichini boshlang.")
#         await state.clear()
#         return

#     try:
#         # Kod orqali login
#         await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)

#         # Session string olish
#         session_string = client.session.save()

#         # Userni bazaga yozish
#         try:
#             await user_login_db(
#                 telegram_id=message.from_user.id,
#                 phone=phone,
#                 session_string=session_string
#             )
#         except TypeError:
#             # Agar funksiya session_string qabul qilmasa
#             await user_login_db(telegram_id=message.from_user.id, phone=phone)

#         await message.answer(
#             "✅ Siz muvaffaqiyatli tizimga kirdingiz!\n\nQaytadan /profile buyrug‘ini yuboring."
#         )

#         await state.clear()
#         await client.disconnect()

#     except errors.SessionPasswordNeededError:
#         await message.answer("🔒 Hisobingizda 2-bosqichli parol yoqilgan. Parolni kiriting:")
#         await state.update_data(client=client, phone=phone)
#         await state.set_state(UserLogin.two_step_password)

#     except errors.PhoneCodeExpiredError:
#         await message.answer("❌ Kod muddati o‘tgan. Iltimos, qayta urinib ko‘ring.")
#         await client.disconnect()
#         await state.clear()

#     except errors.PhoneCodeInvalidError:
#         await message.answer("❌ Kod noto‘g‘ri. Iltimos, to‘g‘ri kodni kiriting.")

#     except Exception as e:
#         print("Code kiritishda xato:", e)
#         await message.answer("❌ Xatolik yuz berdi. Qayta urinib ko‘ring.")
#         await client.disconnect()
#         await state.clear()


# # ===========================================================
# # 5️⃣ IKKI BOSQICHLI PAROL HOLATI
# # ===========================================================
# @router.message(UserLogin.two_step_password)
# async def user_sign_in_two_step_password_handler(message: Message, state: FSMContext):
#     data = await state.get_data()
#     client: TelegramClient = data.get("client")
#     phone: str = data.get("phone")
#     password = message.text.strip()

#     if not client:
#         await message.answer("❌ Sessiya topilmadi. Boshidan /start buyrug‘ini yuboring.")
#         await state.clear()
#         return

#     try:
#         await client.sign_in(password=password)

#         # Session string saqlash
#         session_string = client.session.save()

#         # Userni bazaga yozish
#         try:
#             await user_login_db(
#                 telegram_id=message.from_user.id,
#                 phone=phone,
#                 session_string=session_string
#             )
#         except TypeError:
#             await user_login_db(telegram_id=message.from_user.id, phone=phone)

#         await message.answer("✅ Tizimga muvaffaqiyatli kirdingiz!")
#         await state.clear()
#         await client.disconnect()

#     except errors.PasswordHashInvalidError:
#         await message.answer("❌ Parol noto‘g‘ri. Iltimos qayta kiriting.")
#     except Exception as e:
#         print("Two-step error:", e)
#         await message.answer("❌ Xatolik yuz berdi. Qayta urinib ko‘ring.")
#         await client.disconnect()
#         await state.clear()
