from aiogram import Router

from . import setup_chat, moderate, chat_member, welcome_new_chat_members, admin_updates

router = Router()

router.include_router(setup_chat.router)
router.include_router(moderate.router)
router.include_router(chat_member.router)
router.include_router(welcome_new_chat_members.router)
router.include_router(admin_updates.router)
