from aiogram import Dispatcher, Router

from . import (
    chat_settings,
    change_language,
    change_default_ban_duration,
    change_default_mute_duration,
    change_welcome_message,
    warns,
)


router = Router()

router.include_routers(
    chat_settings.router,
    change_language.router,
    change_default_mute_duration.router,
    change_welcome_message.router,
    warns.router,
)
