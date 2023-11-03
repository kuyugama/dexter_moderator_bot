from aiogram import Dispatcher

from . import (
    warn, unwarn
)


def register_handlers(dp: Dispatcher):
    warn.register_handlers(dp)
    unwarn.register_handlers(dp)
