from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

login_inline_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Ro'yhatdan o'tish 🗂️", callback_data="login")
        ]
    ]
)