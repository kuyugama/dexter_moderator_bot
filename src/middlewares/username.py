from aiogram import types
from aiogram.types import Message

from src.database import Cache
from .custom_base import CustomBaseMiddleware, event


class UsernameSaverMiddleware(CustomBaseMiddleware):
    id2username_template = "id2username:{user_id}"
    username2id_template = "username2id:{username}"

    @classmethod
    async def process_user(cls, user: types.User):
        if not user.username:
            return

        cache = Cache.instance

        new_username = user.username.lower()

        id2username_key = cls.id2username_template.format(user_id=user.id)
        username2id_key = cls.username2id_template.format(username=new_username)

        old_username = await cache.get(id2username_key)

        if old_username != new_username:
            await cache.set(username2id_key, user.id, 600)
            await cache.set(id2username_key, new_username, 600)

    @event
    async def on_pre_process_message(self, message: Message):
        await self.process_user(message.from_user)
