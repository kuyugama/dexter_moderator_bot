from aiogram import types
from aiogram.types import Message

from src.database import Cache
from .custom_base import CustomBaseMiddleware, event


class UsernameSaverMiddleware(CustomBaseMiddleware):
    id2username_template = "id2username:{user_id}"
    username2id_template = "username2id:{username}"

    @staticmethod
    async def process_user(user: types.User):
        cache = Cache.instance
        cls = UsernameSaverMiddleware
        id2username_key = cls.id2username_template.format(user_id=user.id)
        username2id_key = cls.username2id_template.format(username=user.username)

        old_username = await cache.get(id2username_key)

        if old_username != user.username:
            await cache.set(username2id_key, user.id, 600)
            await cache.set(id2username_key, user.username, 600)

    @event
    async def on_pre_process_message(self, message: Message):
        await self.process_user(message.from_user)
