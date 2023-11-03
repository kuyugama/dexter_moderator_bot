from aiogram import Dispatcher

from . import (
    setup_chat,
    moderate,
    chat_member,
    welcome_new_chat_members,
    admin_updates
)


def register_handlers(dp: Dispatcher):
    setup_chat.register_handlers(dp)
    moderate.register_handlers(dp)
    chat_member.register_handlers(dp)
    welcome_new_chat_members.register_handlers(dp)
    admin_updates.register_handlers(dp)
