from aiogram import Dispatcher, Router

from . import warns_settings, change_limit, change_action, change_action_time

router = Router()

router.include_routers(
    warns_settings.router,
    change_limit.router,
    change_action.router,
    change_action_time.router,
)
