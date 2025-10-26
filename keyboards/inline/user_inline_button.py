from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

user_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📨 Habar qo'shish", callback_data="user_message"),
            InlineKeyboardButton(text="🛍️ Paket harid qilish", callback_data="user_paket"),
        ],
        [
            InlineKeyboardButton(text="💰 Balance ni to'ldirish", callback_data="user_balance"),

        ]
    ]
)

user_balance_check = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="user_balance_yes"),
        ],
        [
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="user_balance_no"),
        ]
    ]
)