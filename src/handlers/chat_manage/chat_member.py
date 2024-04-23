from aiogram import Dispatcher, types, Router

from ... import translations, filters
from ...database import models, Cache


router = Router()


def mention(user: types.User) -> str:
    user_mention = user.mention_html()

    user_mention += (
        f"(id<code>{user.id}</code>{f'|@{user.username}' if user.username else ''})"
    )

    return user_mention


@router.message(
    filters.Command(("me", "я", "мі"), prefixes=("!", "/")), filters.NotAnonymous()
)
async def me(message: types.Message, chat: models.Chat):
    member = await Cache.instance.get_member(message.from_user.id, message.chat.id)

    await message.reply(
        text=translations.get_string("member_info.text", chat.language).format(
            user=mention(message.from_user),
            warns=member.warns,
            max_warns=chat.warns_limit,
        )
    )


@router.message(
    filters.Command(("you", "ю"), prefixes=("!", "/")), filters.NotAnonymous()
)
async def another(message: types.Message, chat: models.Chat):
    user = message.from_user
    if message.reply_to_message:
        user = message.reply_to_message.from_user

    member = await Cache.instance.get_member(user.id, message.chat.id)

    if not member:
        return await message.reply(
            text=translations.get_string("member_info.member_not_exists", chat.language)
        )

    await message.reply(
        text=translations.get_string("member_info.text", chat.language).format(
            user=mention(user), warns=member.warns, max_warns=chat.warns_limit
        )
    )
