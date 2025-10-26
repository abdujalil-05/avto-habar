from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from states.user_state import UserBalanceState

import os

from keyboards.inline.user_inline_button import user_menu, user_balance_check
from keyboards.default.cancel_button import cancel_button
from keyboards.inline.admin_panel_inline_keyboard import admin_user_balance_chek

router = Router()

ADMIN = os.getenv("ADMINS")


@router.message(Command("menu"))
async def user_menu_handler(message: Message):
    await message.answer("✨ User menuga hush kelibsiz", reply_markup=user_menu)

@router.callback_query(F.data == "user_balance")
async def user_balance_handler(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Balansingizni qancha summaga to'ldirmoqchisiz ?\n\nMisol uchun: <b>20 000</b> yoki <b>20000</b>.\nFaqat summani kiriting (20 000 so'm yoki 20.000) shaklda kiritish mumkin emas ❗️", parse_mode="HTML")
    await state.set_state(UserBalanceState.summa)


@router.message(UserBalanceState.summa)
async def user_balance_summa_handler(message: Message, state: FSMContext):
    if message.text:
        summa = message.text.strip()
        summa = summa.replace(" ", "")
        if summa.isdigit():
            await state.update_data(summa=int(summa))
            await message.answer("Kiritgan summangiz qabul qilindi ✅")
            await message.answer(
                f"💳 Siz {int(summa):,} so'm to‘ldirishni tanladingiz.\n\n"
                "To‘lovni amalga oshirish uchun quyidagi kartaga pul yuboring:\n\n"
                "💳 Karta raqami:\n`4073 4200 4830 3428`\n"
                "👤 Abdujalil Abdulaxatov\n"
                "📋 Ustiga bosib nusxa oling\n\n"
                "✅ To‘lovni amalga oshirgach, chekni yuboring.\n\n"
                "🚫 *Soxta chek* yoki boshqa narsa yuborsangiz *admin* tomonidan bloklanishingiz mumkin!", parse_mode="Markdown"
            )
            await state.set_state(UserBalanceState.check_photo)

        else:
            await message.answer("Siz hato summa yubordingiz ❌ Iltimos tekshirib qaytadan yuboring", reply_markup= cancel_button)
    else:
        await message.answer("Siz hato summa yubordingiz ❌ Iltimos tekshirib qaytadan yuboring", reply_markup= cancel_button)

@router.message(UserBalanceState.check_photo)
async def user_balance_summa_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    user = message.from_user
    

    if message.photo:
        await message.answer("Yuborgan chekingiz qabul qilindi ✅")
        await message.answer(f"Balansingizni <b>{data['summa']}</b> ga to'ldirmoqchimsiz ?",parse_mode="HTML" , reply_markup=user_balance_check)
        await state.update_data(message_photo= message.photo[-1].file_id)
        await state.set_state(UserBalanceState.check)
  
    elif message.document:
        await message.answer("Yuborgan chekingiz qabul qilindi ✅")
        await message.answer(f"Balansingizni <b>{data['summa']}</b> ga to'ldirmoqchimsiz ?",parse_mode="HTML" , reply_markup=user_balance_check)
        await state.update_data(message_document= message.document.file_id)
        await state.set_state(UserBalanceState.check)
    else:
        await message.answer("Siz hato chek yubordingiz ❌ Iltimos tekshirib qaytadan yuboring") 

@router.callback_query(StateFilter(UserBalanceState.check), F.data == "user_balance_yes")
async def user_balance_confirm_handler(call: CallbackQuery, bot: Bot,  state: FSMContext):
    data = await state.get_data()
    user = call.from_user
    photo_id = data.get("message_photo")
    caption = (
        f"🧾 Chek yubordi: <a href=\"tg://user?id={user.id}\">{user.full_name}</a>\n"
        f"👤 ID: <code>{user.id}</code>\n\n"
        f"To'ldirmoqchi bo'lgan summasi {data.get('summa'):,} so'm"
    )
    user_caption = (
        f"🤵🏻 Ismingiz: <a href=\"tg://user?id={user.id}\">{user.full_name}</a>\n"
        f"👤 ID: <code>{user.id}</code>\n\n"
        f"💰 To'ldirmoqchi bo'lgan summa: {data.get('summa'):,} so'm"
        f"\n\nAdminga habar berildi✅\n⏰ Tez orada sizning chekingizni tasdiqlab balansingizga pul yuboradi"
    )
    
    if photo_id:
        await bot.send_photo(chat_id=ADMIN, photo=photo_id, caption=caption, parse_mode="HTML")
    else:
        await bot.send_document(chat_id=ADMIN, document=data.get("message_document"), caption=caption, parse_mode="HTML")
        await call.message.edit_text(user_caption)



@router.callback_query(F.data == "user_balance_no")
async def user_balance_cancel_handler(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("❌ Amaliyot bekor qilindi")
    await state.clear()







@router.callback_query(F.data == "user_paket")
async def user_paket_handler(call: CallbackQuery):
    pass


@router.callback_query(F.data == "user_message")
async def user_message_handler(call: CallbackQuery):
    pass





