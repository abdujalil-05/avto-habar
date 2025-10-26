from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from keyboards.inline.admin_panel_inline_keyboard import admin_panel_inline_keyborad, admin_user_balance_chek
from keyboards.default.cancel_button import cancel_button
from states.admin_state import AdminDeleteState, AdminUserAddBalance
from data.db.admin.admin import admin_delete_user, admin_user_add_balance_db
from filters.admin_filter import IsAdmin
from data.db.users.user import get_user_by_id


router = Router()







@router.message(IsAdmin(), Command("admin"))
async def admin_panel_handler(message: Message, state: FSMContext):
    await message.answer("👮🏻‍♀️ Admin panelga hush kelibsiz!", reply_markup=admin_panel_inline_keyborad)



@router.callback_query(F.data == "delete_user")
async def admin_delete_user_handler(call: CallbackQuery, state: FSMContext):
    await call.message.answer("🆔 Userni id sini kiriting:", reply_markup=cancel_button)
    await state.set_state(AdminDeleteState.user_id)


@router.message(F.text == "❌ Bekor qilish")
async def cancel_admin_user_delete_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Amaliyot bekor qilindi ✅", reply_markup=ReplyKeyboardRemove())


@router.message(AdminDeleteState.user_id)
async def admin_delete_user_id_handler(message: Message, state: FSMContext):
    try:
        text = (message.text or "").strip()
        if not text:
            await message.answer("Siz hato id kiritdingiz❌ Iltimos tekshirib qaytadan kiriting!")
            return

        try:
            user_id = int(text)
        except ValueError:
            await message.answer("ID faqat raqamlardan iborat bo‘lishi kerak ❌")
            return

        check = await admin_delete_user(user_id)
        if check:
            await message.answer("User va unga bog‘liq xabarlar o‘chirildi ✅", reply_markup=ReplyKeyboardRemove())
            await state.clear()
        else:
            await message.answer("Bunday user mavjud emas ❌ Iltimos tekshirib qaytadan kiriting!")
    
    except Exception as e:
        print("Userni delete qilishda id sini kiritganda hatolik: ", e)
        await state.clear()



@router.callback_query(F.data == "user_add_balance")
async def admin_user_add_balance(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("🆔 Userni id sini kiriting: ")
    await state.set_state(AdminUserAddBalance.user_id)


@router.message(AdminUserAddBalance.user_id)
async def admin_user_add_balance_user_id(message: Message, state: FSMContext):
    user_id = message.text.strip().replace(" ", "")
    if user_id.isdigit():
        user = await get_user_by_id(int(user_id))
        if not user:
            await message.answer("Bunday id li user mavjud emas ❌ Iltimos tekshirib qaytadan kiriting!")
            return
        print("user: ", user)
        print("user balance: ",  user.get("user_balance"))
        caption = (
            f"🤵🏻 User: <a href=\"tg://user?id={user.get('telegram_id')}\">{user.get('name')}</a>\n"
            f"👤 ID: <code>{user.get('telegram_id')}</code>\n\n"
            f"💰 User balansi: {user.get('user_balance')} so'm"
        )
        await message.answer(caption, parse_mode="HTML")
        await message.answer("💳 Userni balansiga qancha pul tashlamoqchisiz: ")
        await state.update_data(user_id=user_id, user_old_balance=user.get('user_balance'))
        await state.set_state(AdminUserAddBalance.summa)
    else:
        await message.answer("Siz xato id kiritdingiz ❌ Iltimos tekshirib qaytadan kiriting")


@router.message(AdminUserAddBalance.summa)
async def admin_user_balance_summa(message: Message, state: FSMContext):
    if message.text:
        summa = message.text.strip()
        summa = summa.replace(" ", "")
        if summa.isdigit():
            await message.answer("Kiritgan summangiz qabul qilindi ✅")
            await state.update_data(summa=summa)
            await message.answer(f"Userni balansini <b>{int(summa):,}</b> ga to'ldirmoqchimsiz ?",parse_mode="HTML" , reply_markup=admin_user_balance_chek)
            await state.set_state(AdminUserAddBalance.check)
        else:
            await message.answer("Siz hato summa yubordingiz ❌ Iltimos tekshirib qaytadan yuboring")
    else:    
        await message.answer("Siz hato summa yubordingiz ❌ Iltimos tekshirib qaytadan yuboring" )
    


@router.callback_query(StateFilter(AdminUserAddBalance.check), F.data == "admin_confirm_balance")
async def admin_user_balance_confirm(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_new_balance = int(data.get("summa")) + int(data.get('user_old_balance'))
    user = await admin_user_add_balance_db(user_id=int(data.get("user_id")), balance=data.get("summa")+data.get('user_old_balance'))
    if user:
        await call.message.edit_text("Userni balanciga muvaffaqiyatli pul qo'shildi ✅")
    else:
        await call.message.edit_text("Userni balanciga pul qo'shilmadi ❌")

@router.callback_query(StateFilter(AdminUserAddBalance.check), F.data == "admin_cancel_balance")
async def admin_user_balance_cancel(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("❌ Amaliyot bekor qilindi")
    await state.clear()