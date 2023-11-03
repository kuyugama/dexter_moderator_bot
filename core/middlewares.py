from sqlalchemy import insert
from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware

from .database import models, CacheSystem
from .utils.types import ExtendedBot, ExtendedMessage
from . import translations


class UsernameSaverMiddleware(BaseMiddleware):
    @staticmethod
    async def process_user(user: types.User, cache: CacheSystem):
        id2username_key = "id2username:{user_id}".format(user_id=user.id)
        username2id_key = "username2id:{username}".format(username=user.username)

        old_username = await cache.get(id2username_key)

        if old_username != user.username:
            await cache.set(username2id_key, user.id, 600)
            await cache.set(id2username_key, user.username, 600)

    async def on_pre_process_message(self, message: ExtendedMessage, *_):
        if not message.from_user:
            return
        await self.process_user(message.from_user, message.bot.cache)


class ChatMiddleware(BaseMiddleware):
    @staticmethod
    async def add_chat(
        bot: ExtendedBot, chat: types.Chat, user: types.User | None = None
    ):
        async with bot.db() as session:
            chat_exists = await bot.cache.get_chat(chat.id)

            if chat_exists:
                return

            language = "en"
            if chat.type == "private" and user:
                language = user.language_code
                if language not in translations.get_languages().keys():
                    language = "en"

            await session.execute(
                insert(models.Chat).values(
                    id=chat.id,
                    is_group=(
                        chat.type in (types.ChatType.GROUP, types.ChatType.SUPERGROUP)
                    ),
                    language=language,
                )
            )

            await session.commit()

    async def on_pre_process_message(self, message: types.Message, *_):
        user = None
        if message.from_user:
            user = message.from_user

        chat = message.chat

        bot = message.bot

        # noinspection PyTypeChecker
        await self.add_chat(bot, chat, user)

    async def on_pre_process_chat_member(
        self, chat_member: types.ChatMemberUpdated, *_
    ):
        chat = chat_member.chat

        bot = chat_member.bot

        # noinspection PyTypeChecker
        await self.add_chat(bot, chat)


class MemberMiddleware(BaseMiddleware):
    @staticmethod
    async def add_member(bot: ExtendedBot, chat: types.Chat, user: types.User):
        async with bot.db() as session:
            member_exists = await bot.cache.get_member(user.id, chat.id)

            if member_exists:
                return

            await session.execute(
                insert(models.Member).values(user_id=user.id, chat_id=chat.id, warns=0)
            )
            await session.commit()

    async def on_pre_process_message(self, message: types.Message, *_):
        chat = message.chat
        if not message.from_user:
            return
        user = message.from_user

        bot = message.bot

        # noinspection PyTypeChecker
        await self.add_member(bot, chat, user)

    async def on_pre_process_chat_member(
        self, chat_member: types.ChatMemberUpdated, *_
    ):
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
        bot = chat_member.bot

        # noinspection PyTypeChecker
        await self.add_member(bot, chat, new_member.user)
