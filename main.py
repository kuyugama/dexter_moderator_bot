from asyncio import run as run_async

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage

from src import config, middlewares, handlers, database, filters


bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))

storage = RedisStorage(database.redis)

dp = Dispatcher(storage=storage)


@dp.message(filters.Command("drop_states"))
async def drop_states(message):
    states = await database.redis.keys("fsm:*:*:state")

    if not states:
        return await message.reply(text="No states found")

    await database.redis.delete(*states)

    await message.reply(text="Dropped all states")


@dp.message(filters.Command("drop_caches"))
async def invalidate_caches(message):
    caches = await database.redis.keys("cache:*")

    if not caches:
        return await message.reply(text="No caches found")

    await database.redis.delete(*caches)

    await message.reply(text=f"Dropped {len(caches)} records of cache")


@dp.startup()
async def on_startup():
    await database.init()

    database.Cache.init_singleton(database.session, database.redis)


async def main():
    middlewares.ChatMiddleware().register(dp, True)
    middlewares.MemberMiddleware().register(dp, True)
    middlewares.UsernameSaverMiddleware().register(dp, True)

    dp.include_router(handlers.router)

    await bot.delete_webhook(drop_pending_updates=True)
    print("[bot] All updates skipped!")
    print("[bot] Polling started!")
    print("[bot] Username: ", (await bot.me()).username)
    await dp.start_polling(
        bot,
        allowed_updates=["chat_member", "message", "callback_query", "my_chat_member"],
    )


if __name__ == "__main__":
    run_async(main())
