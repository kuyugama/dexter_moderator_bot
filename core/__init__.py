from aiogram import Dispatcher

from . import database


async def on_startup(dp: Dispatcher):
    postgresql_connection = await database.init()
    dp.bot.db = postgresql_connection
    dp.bot.cache = database.CacheSystem(postgresql_connection, database.redis)
