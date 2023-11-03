import asyncio
from time import time

from aiogram import Dispatcher, types
from aiogram.utils import exceptions
from sqlalchemy import select

from ..database import models
from .. import filters, translations
from ..utils import strings


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(
        mail,
        filters.Command(("mail", "розіслати"), prefixes=("/", "!")),
        filters.LocalBotAdmin(),
    )


async def mail(message: types.Message):
    chat = await message.bot.cache.get_chat(message.chat.id)
    if not message.reply_to_message:
        return await message.reply(
            text=translations.get_string("mail.reply_required", language=chat.language)
        )
    async with message.bot.db() as session:
        chats: list[models.Chat] = (
            (await session.execute(select(models.Chat).where(models.Chat.is_group)))
            .scalars()
            .all()
        )

    if len(chats) < 2:
        return await message.reply(
            text=translations.get_string("mail.no_chats", language=chat.language)
        )

    replied_message = message.reply_to_message

    approximate_required_time = (len(chats) - 1) * 8

    info_message = await replied_message.reply(
        text=translations.get_string("mail.start", language=chat.language).format(
            time=strings.beautify_time(
                seconds=approximate_required_time, language=chat.language,
            ),
            chats_count=len(chats) - 1
        )
    )

    start_time = time()

    error_chats_count = 0

    for to_chat in chats:
        if to_chat.id == chat.id:
            continue
        try:
            await message.bot.send_message(
                text=translations.get_string(
                    "mail.notification",
                    language=to_chat.language
                ),
                chat_id=to_chat.id
            )
            await asyncio.sleep(4)
            await replied_message.forward(
                chat_id=to_chat.id
            )

            await asyncio.sleep(4)
        except (exceptions.ChatNotFound, exceptions.BotKicked, exceptions.MigrateToChat):
            error_chats_count += 1
            continue

    await info_message.reply(
        text=translations.get_string(
            "mail.success",
            language=chat.language
        ).format(
            time=strings.beautify_time(seconds=round(time() - start_time), language=chat.language),
            error_chats_count=error_chats_count
        )
    )