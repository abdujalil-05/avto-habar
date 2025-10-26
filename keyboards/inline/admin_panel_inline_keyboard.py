from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

admin_panel_inline_keyborad = InlineKeyboardMarkup(
    inline_keyboard= [
        [
            InlineKeyboardButton(text="Balance To'ldirish 💰", callback_data="user_add_balance"),
            InlineKeyboardButton(text="Balance Ayirish ➖💰", callback_data="user_minus_balance"),
        ],
        [
            InlineKeyboardButton(text="Userni bazadan o'chirish 🗑️", callback_data="delete_user"),
        ]
    ]
)

admin_user_balance_chek = InlineKeyboardMarkup(
    inline_keyboard= [
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="admin_confirm_balance"),
        ],
        [
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_cancel_balance"),
        ]
    ]
)