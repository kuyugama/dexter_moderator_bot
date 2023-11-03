from aiogram import Dispatcher

from . import (
    chat_settings,
    change_language,
    change_default_ban_duration,
    change_default_mute_duration,
    change_welcome_message,
    warns
)


def register_handlers(dp: Dispatcher):
    chat_settings.register_handlers(dp)
    change_language.register_handlers(dp)
    change_default_ban_duration.register_handlers(dp)
    change_default_mute_duration.register_handlers(dp)
    change_welcome_message.register_handlers(dp)

    warns.register_handlers(dp)
