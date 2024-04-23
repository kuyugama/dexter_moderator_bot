from aiogram import Dispatcher, Router

from . import warn, unwarn

router = Router()

router.include_routers(warn.router, unwarn.router)
