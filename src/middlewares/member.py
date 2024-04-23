from aiogram import Bot, types
from sqlalchemy import insert

from src.database import models, Cache
from .custom_base import CustomBaseMiddleware, event, ChatMember
from .. import database


class MemberMiddleware(CustomBaseMiddleware):
    @staticmethod
    async def add_member(chat: types.Chat, user: types.User):
        async with database.session() as session:
            member_exists = await Cache.instance.get_member(user.id, chat.id)

            if member_exists:
                return

            await session.execute(
                insert(models.Member).values(user_id=user.id, chat_id=chat.id, warns=0)
            )
            await session.commit()

    @event
    async def message(self, message: types.Message):
        chat = message.chat
        if not message.from_user:
            return
        user = message.from_user

        # noinspection PyTypeChecker
        await self.add_member(chat, user)

    @event
    async def chat_member(self, chat_member: ChatMember):
        if not (
            chat_member.chat.type in ("group", "supergroup")
            and (
                chat_member.old_chat_member
                and chat_member.old_chat_member.status in ("left", "kicked")
            )
            and (
                chat_member.new_chat_member
                and chat_member.new_chat_member.status == "member"
            )
        ):
            return

        chat = chat_member.chat
        new_member = chat_member.new_chat_member

        # noinspection PyTypeChecker
        await self.add_member(chat, new_member.user)
