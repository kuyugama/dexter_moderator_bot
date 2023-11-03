from aiogram import Dispatcher

from . import (
    warns_settings,
    change_limit,
    change_action,
    change_action_time
)


def register_handlers(dp: Dispatcher):
    warns_settings.register_handlers(dp)

    change_limit.register_handlers(dp)
    change_action.register_handlers(dp)
    change_action_time.register_handlers(dp)