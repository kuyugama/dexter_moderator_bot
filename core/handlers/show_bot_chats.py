import asyncio
from io import BytesIO

from sqlalchemy import select, delete
from aiogram import Dispatcher, exceptions

from ..utils import types

from ..database import models
from .. import filters


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(
        show_chats,
        filters.Command(("show_chats",)),
        lambda m: m.from_user.id in (867531027, 584916899),
    )


async def show_chats(message: types.ExtendedMessage):

    sent = await message.reply(text="Збір даних...")

    async with message.bot.db() as session:
        chats: list[models.Chat] = (
            (await session.execute(select(models.Chat))).scalars().all()
        )

    sent = await sent.edit_text(
        text=sent.text
        + f"\nОтримано {len(chats)} з бази даних. Перевірка їх в телеграмі.."
    )

    checked_chats = [
        # models.Chat
    ]

    file = BytesIO()
    file.name = "chats.txt"

    index = 1

    for chat in chats:
        try:
            chat_from_tg = await message.bot.get_chat(chat.id)
            bot_member = await chat_from_tg.get_member(message.bot.id)
        except (exceptions.BotKicked, exceptions.ChatNotFound, exceptions.Unauthorized, exceptions.BotBlocked):
            async with message.bot.db() as session:
                await session.execute(
                    delete(models.Chat).where(models.Chat.id == chat.id)
                )
                await session.commit()
                continue

        try:
            if chat.is_group and not chat_from_tg.invite_link:
                chat_from_tg.invite_link = await chat_from_tg.create_invite_link()
        except:
            chat_from_tg.invite_link = "Can't create link"

        chat_info = (
            f"{index}. [{chat.id}] {chat_from_tg.full_name}\n"
            f"Is group: {chat.is_group}\n"
            f"Language: {chat.language}\n"
            f"Bot is admin: {bot_member.is_chat_admin()}\n"
            f"Username: {chat_from_tg.username}\n"
            + (
                f"Invite link: {chat_from_tg.invite_link}\n"
                f"Count of members: {await chat_from_tg.get_members_count()}"
                if chat.is_group
                else ""
            )
        )

        file.write((chat_info + "\n\n").encode())

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

    file.seek(0)
    await sent.reply_document(
        file
    )
