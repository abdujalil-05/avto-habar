from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import Command

from data.db.users.user import add_user, get_user


router = Router()


@router.message(Command("start"))
async def user_bot_start(message: Message):
    user = message.from_user
    text = f"""
✨ <b>Assalomu alaykum, <a href="tg://user?id={user.id}">{user.full_name}</a>!</b> ✨

🤖 <b>Avto Message Bot</b> — bu sizning xabarlaringizni <u>avtomatik ravishda</u> yuboradigan ishonchli yordamchingiz 🚀  

📌 <b>Botning asosiy imkoniyatlari:</b>  
1️⃣ Oddiy <b>matnli xabar</b> yuborish  
2️⃣ <b>Rasm + matn</b> (banner + izoh) yuborish  
3️⃣ Xabarlarni <b>oldindan rejalashtirish</b> ⏱️  
4️⃣ Bir nechta guruhlarga bir vaqtda yuborish 📣  

💡 <b>Nega Avto Message Bot?</b>  
✔️ Vaqtingizni tejaydi  
✔️ Xatoliklarni kamaytiradi  
✔️ Jarayonlarni to‘liq avtomatlashtiradi  

👇 Boshlash uchun pastdagi menyudan foydalaning:  
• 🗂️ <b>Boshlash</b> - /free_message
  

⚡ <i>Avto Message Bot bilan ishlash — tez, qulay va samarali!</i>
"""

    await message.answer(text, parse_mode="HTML")

    try:
        data = await get_user(telegram_id=user.id, username=user.username, name=user.full_name)
        # print("data: ", data)
        if not data:
            print("aaaaaa")
            await add_user(telegram_id=user.id, username=user.username, name=user.full_name)
            free_text = """
🤩 Siz botdan birinchi marta foydalanayotganingiz uchun <b>bepulga</b> avto habar ulashingiz mumkin! 🎉

• ✍️ <b>Free message</b> ni aktivlashtirish uchun /free_message buyrug‘ini yuboring.
"""
            await message.answer(free_text, parse_mode="HTML")
        else:
            print("bbbbbb")
            # Faqat yangi foydalanuvchi bo‘lsa, xabar yuboriladi
            if not data.get("free_message"):
                free_text = """
🤩 Siz botdan birinchi marta foydalanayotganingiz uchun <b>bepulga</b> avto habar ulashingiz mumkin! 🎉

• ✍️ <b>Free message</b> ni aktivlashtirish uchun /free_message buyrug‘ini yuboring.
"""
                await message.answer(free_text, parse_mode="HTML")

    except Exception as e:
        print("User qo'shish/olishda hatolik:", e)
