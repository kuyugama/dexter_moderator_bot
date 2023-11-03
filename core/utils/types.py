from aiogram.types import *
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot

from .. import database


class ExtendedBot(Bot):
    @staticmethod
    def db() -> AsyncSession:
        return AsyncSession()

    cache = database.CacheSystem


class ExtendedMessage(Message):
    bot: ExtendedBot


class ExtendedCallbackQuery(CallbackQuery):
    bot: ExtendedBot


class ExtendedChatMemberUpdated(ChatMemberUpdated):
    bot: ExtendedBot
