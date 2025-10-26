from aiogram import Router
from .admin_panel import router as admin_panel_router

admins = Router()
admins.include_router(admin_panel_router)
