import typing
from asyncio import current_task
import json

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from . import models, config

redis = Redis(
    host=config.REDIS_ADDRESS,
    port=config.REDIS_PORT,
    username=config.REDIS_USERNAME,
    password=config.REDIS_PASSWORD,
    db=config.REDIS_DB,
)


async def init():
    url = URL.create(
        drivername="postgresql+asyncpg",
        username=config.DB_USERNAME,
        password=config.DB_PASSWORD,
        host=config.DB_ADDRESS,
        port=config.DB_PORT,
        database=config.DB_NAME
    )

    engine = create_async_engine(url, echo=False, pool_pre_ping=True)

    async with engine.begin() as conn:
        await conn.run_sync(models.METADATA.create_all)

    async_session_factory = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    async_session = async_scoped_session(async_session_factory, scopefunc=current_task)

    return async_session


class CacheSystem:
    def __init__(self, postgresql_connection, redis_connection):
        self._database = postgresql_connection
        self._redis: aioredis.Redis = redis_connection

    async def get_chat(self, chat_id: int) -> models.Chat | None:

        value = await self._redis.get(f"cache:chat:{chat_id}")

        if not value:
            async with self._database() as session:
                chat = (
                    (
                        await session.execute(
                            select(models.Chat).where(models.Chat.id == chat_id)
                        )
                    )
                    .scalars()
                    .first()
                )

            if chat:
                await self._redis.setex(
                    f"cache:chat:{chat_id}",
                    3600,
                    json.dumps(chat.to_dict(), ensure_ascii=False),
                )

        else:
            chat = models.Chat.from_dict(json.loads(value))

        return chat

    async def refresh_chat(self, chat_id: int) -> bool:
        result = await self._redis.delete(f"cache:chat:{chat_id}")

        return result

    async def get_member(self, user_id: int, chat_id: int) -> models.Member | None:

        value = await self._redis.get(f"cache:user:{user_id}:{chat_id}")

        if not value:
            async with self._database() as session:
                user = (
                    (
                        await session.execute(
                            select(models.Member).where(
                                models.Member.user_id == user_id,
                                models.Member.chat_id == chat_id,
                            )
                        )
                    )
                    .scalars()
                    .first()
                )

            if user:
                await self._redis.setex(
                    f"cache:user:{user_id}:{chat_id}",
                    3600,
                    json.dumps(user.to_dict(), ensure_ascii=False),
                )

        else:
            user = models.Member.from_dict(json.loads(value))

        return user

    async def refresh_member(self, user_id: int, chat_id: int) -> bool:
        result = await self._redis.delete(f"cache:user:{user_id}:{chat_id}")

        return result

    async def set(self, name: str, value, expire_seconds: int = 300) -> bool:
        return await self._redis.setex(
            f"cache:{name}", expire_seconds, json.dumps(value, ensure_ascii=False)
        )

    async def get(self, name: str, default=None) -> typing.Any:
        value = await self._redis.get(f"cache:{name}")
        if not value:
            return default
        return json.loads(value)

    async def remove(self, name: str):
        return await self._redis.delete(f"cache:{name}")
