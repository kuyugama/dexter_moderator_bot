import asyncio
from io import BytesIO
from typing import Sequence

from sqlalchemy import select, delete
from aiogram import Router, exceptions, types

from ..database import models
from .. import filters, database

router = Router()


@router.message(filters.Command(("show_chats",)), filters.LocalBotAdmin())
async def show_chats(message: types.Message):

    sent = await message.reply(text="Збір даних...")

    async with database.session() as session:
        chats: Sequence[models.Chat] = (
            await session.scalars(select(models.Chat))
        ).all()

    sent = await sent.edit_text(
        text=sent.text
        + f"\nОтримано {len(chats)} з бази даних. Перевірка їх в телеграмі.."
    )

    checked_chats = [
        # models.Chat
    ]

    content = b""

    index = 1

    for chat in chats:
        try:
            chat_from_tg = await message.bot.get_chat(chat.id)
            bot_member = await chat_from_tg.get_member(message.bot.id)
        except exceptions.TelegramBadRequest:
            async with database.session() as session:
                await session.execute(
                    delete(models.Chat).where(models.Chat.id == chat.id)
                )
                await session.commit()
                continue
        invite_link = chat_from_tg.invite_link
        try:
            if chat.is_group and not chat_from_tg.invite_link:
                invite_link = await chat_from_tg.create_invite_link()
        except exceptions.TelegramBadRequest:
            invite_link = "Can't create link"

        chat_info = (
            f"{index}. [{chat.id}] {chat_from_tg.full_name}\n"
            f"Is group: {chat.is_group}\n"
            f"Language: {chat.language}\n"
            f"Bot is admin: {isinstance(bot_member, (types.ChatMemberOwner, types.ChatMemberAdministrator))}\n"
            f"Username: {chat_from_tg.username}\n"
            + (
                f"Invite link: {invite_link}\n"
                f"Count of members: {await chat_from_tg.get_member_count()}"
                if chat.is_group
                else ""
            )
        )

        content += (chat_info + "\n\n").encode()

        checked_chats.append(chat)
        index += 1
        await asyncio.sleep(1.4)

    users = list(filter(lambda chat: not chat.is_group, checked_chats))
    groups = list(filter(lambda chat: chat.is_group, checked_chats))

    # noinspection PyUnresolvedReferences
    await sent.edit_text(
        text=sent.text + "\nЧати:\n"
        f"З користувачами: {len(users)}\n"
        f"Групи: {len(groups)}"
    )

    await sent.reply_document(types.BufferedInputFile(content, "chats.txt"))
