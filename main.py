from asyncio import run as run_async

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from core import on_startup, config, middlewares, handlers, database, filters


async def drop_states(message):
    states = await database.redis.keys("fsm:*:*:state")

    if not states:
        return await message.reply(text="No states found")

    await database.redis.delete(*states)

    await message.reply(text="Dropped all states")


async def invalidate_caches(message):
    caches = await database.redis.keys("cache:*")

    if not caches:
        return await message.reply(text="No caches found")

    await database.redis.delete(*caches)

    await message.reply(text=f"Dropped {len(caches)} records of cache")


async def main():
    bot = Bot(token=config.BOT_TOKEN, parse_mode="HTML")

    storage = RedisStorage2(
        host=database.config.REDIS_ADDRESS,
        port=database.config.REDIS_PORT,
        username=database.config.REDIS_USERNAME,
        password=database.config.REDIS_PASSWORD,
        db=database.config.REDIS_DB,
    )

    dp = Dispatcher(bot, storage=storage)
    dp.setup_middleware(middlewares.ChatMiddleware())
    dp.setup_middleware(middlewares.MemberMiddleware())
    dp.setup_middleware(middlewares.UsernameSaverMiddleware())
    dp.register_message_handler(drop_states, filters.Command("drop_states"), state="*")
    dp.register_message_handler(
        invalidate_caches, filters.Command("drop_caches"), state="*"
    )
    handlers.register_handlers(dp)

    await on_startup(dp)

    await bot.delete_webhook(drop_pending_updates=True)
    print("[bot] All updates skipped!")
    print("[bot] Polling started!")
    print("[bot] Username: ", (await bot.me).username)
    await dp.start_polling(allowed_updates=["chat_member", "message", "callback_query", "my_chat_member"])


if __name__ == "__main__":
    run_async(main())
