from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

message_interval = InlineKeyboardMarkup(
    inline_keyboard= [
        [
            InlineKeyboardButton(text="5", callback_data="message_interval,5"),
            InlineKeyboardButton(text="10", callback_data="message_interval,10"),
            InlineKeyboardButton(text="15", callback_data="message_interval,15"),
        ],
        [
            InlineKeyboardButton(text="30", callback_data="message_interval,30"),
            InlineKeyboardButton(text="45", callback_data="message_interval,45"),
            InlineKeyboardButton(text="60", callback_data="message_interval,60"),
        ],
        [
            InlineKeyboardButton(text="1440", callback_data="message_interval,1440"),

        ],
    ]
)