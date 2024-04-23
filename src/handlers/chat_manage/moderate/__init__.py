from aiogram import Router

from . import mute, ban, kick, pardon, warns

router = Router()
router.include_routers(mute.router, ban.router, kick.router, pardon.router)

router.include_router(warns.router)
