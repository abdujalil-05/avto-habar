from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


cancel_button = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ Bekor qilish")]
    ],
    resize_keyboard=True
)