import json
import typing
from datetime import datetime

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)

from . import models, config

redis = Redis(
    host=config.REDIS_ADDRESS,
    port=config.REDIS_PORT,
    username=config.REDIS_USERNAME,
    password=config.REDIS_PASSWORD,
    db=config.REDIS_DB,
)

_MAKER: async_sessionmaker | None = None


async def init():
    global _MAKER
    url = URL.create(
        drivername="postgresql+asyncpg",
        username=config.DB_USERNAME,
        password=config.DB_PASSWORD,
        host=config.DB_ADDRESS,
        port=config.DB_PORT,
        database=config.DB_NAME,
    )

    engine = create_async_engine(url, echo=False, pool_pre_ping=True)

    async with engine.begin() as conn:
        await conn.run_sync(models.METADATA.create_all)

    _MAKER = async_sessionmaker(engine, expire_on_commit=False)


def session() -> AsyncSession:
    return _MAKER()


class Cache:
    instance: "Cache" = None

    def __init__(
        self, session_maker: typing.Callable[[], AsyncSession], redis_client: Redis
    ):
        self._database = session_maker
        self._redis: Redis = redis_client

    @classmethod
    def init_singleton(
        cls, session_maker: typing.Callable[[], AsyncSession], redis_client: Redis
    ):
        cls.instance = cls(session_maker, redis_client)
        return cls.instance

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
        def default(v: typing.Any) -> typing.Any:
            if isinstance(v, datetime):
                return v.timestamp()

        return await self._redis.setex(
            f"cache:{name}",
            expire_seconds,
            json.dumps(value, ensure_ascii=False, default=default),
        )

    async def get(self, name: str, default=None) -> typing.Any:
        value = await self._redis.get(f"cache:{name}")
        if not value:
            return default
        return json.loads(value)

    async def remove(self, name: str):
        return await self._redis.delete(f"cache:{name}")
