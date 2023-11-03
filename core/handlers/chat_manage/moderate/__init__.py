from aiogram import Dispatcher


from . import (
    mute, ban, kick, pardon, warns
)


def register_handlers(dp: Dispatcher):
    mute.register_handlers(dp)
    ban.register_handlers(dp)
    kick.register_handlers(dp)
    pardon.register_handlers(dp)

    warns.register_handlers(dp)
