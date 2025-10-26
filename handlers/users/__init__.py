from aiogram import Router
from .user_start import router as user_start_router
from .free_message import router as free_message_router
from .login_handler import router as login_handler_router
from .message_interval_and_groups import router as message_interval_and_groups_router
# from .user_menu import router as user_menu_router

users = Router()
users.include_router(user_start_router)
users.include_router(free_message_router)
users.include_router(login_handler_router)
users.include_router(message_interval_and_groups_router)
# users.include_router(user_menu_router)
