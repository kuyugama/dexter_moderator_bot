from aiogram import Router, types
from sqlalchemy import delete

from ... import translations, database
from ...database import models, Cache

router = Router()


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


async def was_kicked_filter(chat_member: types.ChatMemberUpdated):
    return (
        chat_member.new_chat_member and chat_member.new_chat_member.status == "kicked"
    )


@router.my_chat_member(was_kicked_filter)
async def me_was_kicked(chat_member: types.ChatMemberUpdated):
    chat_id = chat_member.chat.id

    async with database.session() as session:
        await session.execute(delete(models.Chat).where(models.Chat.id == chat_id))
        await session.commit()

    await Cache.instance.refresh_chat(chat_id)


@router.my_chat_member(new_chat_admin_filter)
async def me_new_chat_admin(chat_member: types.ChatMemberUpdated, chat: models.Chat):
    new_admin = chat_member.new_chat_member

    await Cache.instance.set(
        f"chat_bot:{chat_member.chat.id}", new_admin.model_dump(), 600
    )

    if chat_member.old_chat_member.status in (
        "member",
        "restricted",
    ):
        await chat_member.bot.send_message(
            chat_id=chat_member.chat.id,
            text=translations.get_string("bot_added_admin_rights", chat.language),
        )


@router.my_chat_member(removed_chat_admin_filter)
async def me_removed_chat_admin(chat_member: types.ChatMemberUpdated):

    cache = Cache.instance

    chat = await cache.get_chat(chat_member.chat.id)

    await cache.set(
        f"chat_bot:{chat_member.chat.id}",
        chat_member.new_chat_member.model_dump() if chat_member.new_chat_member else {},
        600,
    )

    if chat_member.new_chat_member.status != "kicked":
        await chat_member.bot.send_message(
            chat_id=chat_member.chat.id,
            text=translations.get_string("bot_removed_admin_rights", chat.language),
        )


@router.chat_member(new_chat_admin_filter)
async def new_chat_admin(chat_member: types.ChatMemberUpdated):
    new_admin = chat_member.new_chat_member

    cache = Cache.instance

    chat_administrators: list[dict] = await cache.get(
        f"chat_administrators:{chat_member.chat.id}", []
    )

    if new_admin not in list(map(lambda x: x["id"], chat_administrators)):
        chat_administrators.append(
            dict(id=new_admin.user.id, can_restrict=new_admin.can_restrict_members)
        )
        await cache.set(
            f"chat_administrators:{chat_member.chat.id}", chat_administrators, 600
        )


@router.chat_member(removed_chat_admin_filter)
async def removed_chat_admin(chat_member: types.ChatMemberUpdated):
    removed_admin = chat_member.old_chat_member

    cache = Cache.instance

    chat_administrators: list[int] = await cache.get(
        f"chat_administrators:{chat_member.chat.id}", []
    )

    if removed_admin in chat_administrators:
        chat_administrators.remove(removed_admin.user.id)
        await cache.set(
            f"chat_administrators:{chat_member.chat.id}", chat_administrators, 600
        )
