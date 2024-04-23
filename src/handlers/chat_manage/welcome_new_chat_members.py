from aiogram import types, Router

from src.database import Cache, models

router = Router()


@router.chat_member(
    lambda chat_member: (
        chat_member.chat.type in ("group", "supergroup")
        and (
            chat_member.old_chat_member
            and chat_member.old_chat_member.status in ("left", "kicked")
        )
        and (
            chat_member.new_chat_member
            and chat_member.new_chat_member.status == "member"
        )
    )
)
async def welcome(chat_member: types.ChatMemberUpdated, chat: models.Chat):

    new_member = chat_member.new_chat_member

    if not chat.new_participant_greeting:
        return

    await chat_member.bot.send_message(
        text=chat.new_participant_greeting.format(
            chat=chat_member.chat.title, user=new_member.user.mention_html()
        ),
        chat_id=chat_member.chat.id,
    )
