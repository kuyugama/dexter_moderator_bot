from typing import Any

from aiogram import Bot, types
from sqlalchemy import insert

from .custom_base import CustomBaseMiddleware, event, ChatMember, MyChatMember
from .. import translations, database
from ..database import Cache


class ChatMiddleware(CustomBaseMiddleware):
    @staticmethod
    async def add_chat(chat: types.Chat, user: types.User | None = None):
        async with database.session() as session:
            existing_chat = await Cache.instance.get_chat(chat.id)

            if existing_chat:
                return existing_chat

            language = "en"
            if chat.type == "private" and user:
                language = user.language_code
                if language not in translations.get_languages().keys():
                    language = "en"

            chat = await session.scalar(
                insert(database.models.Chat)
                .values(
                    id=chat.id,
                    is_group=(chat.type in ("group", "supergroup")),
                    language=language,
                    new_participant_greeting="",
                )
                .returning(database.models.Chat)
            )

            await session.commit()

            return chat

    @event
    async def message(self, message: types.Message, data: dict[str, Any]):
        data.update(chat=await self.add_chat(message.chat, message.from_user))

    @event
    async def chat_member(
        self, chat_member: ChatMember | MyChatMember, data: dict[str, Any]
    ):
        data.update(chat=await self.add_chat(chat_member.chat))

    @event
    async def callback_query(self, query: types.CallbackQuery, data: dict[str, Any]):
        data.update(chat=await self.add_chat(query.message.chat))
