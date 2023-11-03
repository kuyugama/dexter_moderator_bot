from aiogram import Dispatcher, types


def register_handlers(dp: Dispatcher):
    dp.register_chat_member_handler(
        welcome,
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


async def welcome(chat_member: types.ChatMemberUpdated):

    new_member = chat_member.new_chat_member

    chat = await chat_member.bot.cache.get_chat(chat_member.chat.id)

    if not chat.new_participant_greeting:
        return

    await chat_member.bot.send_message(
        text=chat.new_participant_greeting.format(
            chat=chat_member.chat.title,
            user=new_member.user.get_mention(as_html=True)
        ),
        chat_id=chat_member.chat.id
    )
