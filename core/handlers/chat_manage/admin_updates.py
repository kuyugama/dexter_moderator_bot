from aiogram import Dispatcher
from sqlalchemy import delete

from ...utils import types
from ...database import models
from ... import translations


def register_handlers(dp: Dispatcher):
    dp.register_chat_member_handler(new_chat_admin, new_chat_admin_filter)
    dp.register_chat_member_handler(removed_chat_admin, removed_chat_admin_filter)

    dp.register_my_chat_member_handler(me_new_chat_admin, new_chat_admin_filter)
    dp.register_my_chat_member_handler(me_removed_chat_admin, removed_chat_admin_filter)
    dp.register_my_chat_member_handler(me_was_kicked, me_was_kicked_filter)


async def new_chat_admin_filter(chat_member: types.ChatMemberUpdated):

    return (
        chat_member.old_chat_member
        and chat_member.old_chat_member.status not in ("creator", "administrator")
    ) and (
        chat_member.new_chat_member
        and chat_member.new_chat_member.status in ("creator", "administrator")
    )


async def removed_chat_admin_filter(chat_member: types.ChatMemberUpdated):

    return (
        chat_member.old_chat_member
        and chat_member.old_chat_member.status in ("creator", "administrator")
    ) and (
        chat_member.new_chat_member
        and chat_member.new_chat_member.status not in ("creator", "administrator")
    )


async def me_was_kicked_filter(chat_member: types.ChatMemberUpdated):
    return (
        chat_member.new_chat_member
        and chat_member.new_chat_member.status == "kicked"
    )


async def me_was_kicked(chat_member: types.ChatMemberUpdated):
    chat_id = chat_member.chat.id

    cache = chat_member.bot.cache

    async with chat_member.bot.db() as session:
        await session.execute(
            delete(
                models.Chat
            ).where(
                models.Chat.id == chat_id
            )
        )
        await session.commit()

    await cache.refresh_chat(chat_id)


async def me_new_chat_admin(chat_member: types.ExtendedChatMemberUpdated):
    new_admin = chat_member.new_chat_member

    cache = chat_member.bot.cache

    await cache.set(f"chat_bot:{chat_member.chat.id}", new_admin.to_python(), 600)


async def me_removed_chat_admin(chat_member: types.ExtendedChatMemberUpdated):

    cache = chat_member.bot.cache

    chat = await cache.get_chat(chat_member.chat.id)

    await cache.set(
        f"chat_bot:{chat_member.chat.id}",
        chat_member.new_chat_member.to_python()
        if chat_member.new_chat_member
        else {},
        600,
    )

    if chat_member.new_chat_member.status != "kicked":
        await chat_member.bot.send_message(
            chat_id=chat_member.chat.id,
            text=translations.get_string("bot_removed_admin_rights", chat.language),
        )


async def new_chat_admin(chat_member: types.ExtendedChatMemberUpdated):
    new_admin = chat_member.new_chat_member

    cache = chat_member.bot.cache

    chat_administrators: list[dict] = await cache.get(
        f"chat_administrators:{chat_member.chat.id}", []
    )

    if new_admin not in list(map(lambda x: x["id"], chat_administrators)):
        chat_administrators.append(dict(id=new_admin.user.id, can_restrict=new_admin.can_restrict_members))
        await cache.set(
            f"chat_administrators:{chat_member.chat.id}", chat_administrators, 600
        )


async def removed_chat_admin(chat_member: types.ExtendedChatMemberUpdated):
    removed_admin = chat_member.old_chat_member

    cache = chat_member.bot.cache

    chat_administrators: list[int] = await cache.get(
        f"chat_administrators:{chat_member.chat.id}", []
    )

    if removed_admin in chat_administrators:
        chat_administrators.remove(removed_admin.user.id)
        await cache.set(
            f"chat_administrators:{chat_member.chat.id}", chat_administrators, 600
        )
