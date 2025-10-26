from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

free_message_menu = InlineKeyboardMarkup(
    inline_keyboard= [
        [
            InlineKeyboardButton(text="📜 Oddiy habar qo'shish", callback_data="free_message_standart"),
        ],
        [
            InlineKeyboardButton(text="🌆 Rasmli habar yuborish", callback_data="free_message_photo"),
        ],
       
    ]
)

free_select = InlineKeyboardMarkup(
    inline_keyboard= [
        [
            InlineKeyboardButton(text="O'chirish 🗑️", callback_data="free_delete_message"),
        ],
        [
            InlineKeyboardButton(text="Bekor qilish ❌", callback_data="free_cancel"),
        ],
       
    ]
)

