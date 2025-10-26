from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from data.db.config.config import BOT_TOKEN

# Botni yaratishda default xossalarini beramiz
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher()
