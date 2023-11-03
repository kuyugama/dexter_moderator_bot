from aiogram import Dispatcher, types

from ... import translations, filters


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(
        me,
        filters.Command(
            ("me", "ми", "мі"),
            prefixes=("!", "/")
        ),
        filters.NotAnonymous()
    )

    dp.register_message_handler(
        another,
        filters.Command(
            ("you", "ю"),
            prefixes=("!", "/")
        ),
        filters.NotAnonymous()
    )


def mention(user: types.User) -> str:
    user_mention = user.get_mention(as_html=True)

    if user.username:
        user_mention += f"(@{user.username})"
    else:
        user_mention += f"(id<code>{user.id}</code>)"

    return user_mention


async def me(message: types.Message):
    chat = await message.bot.cache.get_chat(
        message.chat.id
    )
    member = await message.bot.cache.get_member(
        message.from_user.id,
        message.chat.id
    )

    await message.reply(
        text=translations.get_string(
            "member_info.text",
            chat.language
        ).format(
            user=mention(message.from_user),
            warns=member.warns,
            max_warns=chat.warns_limit
        )
    )


async def another(message: types.Message):
    user = message.from_user
    if message.reply_to_message:
        user = message.reply_to_message.from_user

    chat = await message.bot.cache.get_chat(
        message.chat.id
    )
    member = await message.bot.cache.get_member(
        user.id,
        message.chat.id
    )

    if not member:
        return await message.reply(
            text=translations.get_string(
                "member_info.member_not_exists",
                chat.language
            )
        )

    await message.reply(
        text=translations.get_string(
            "member_info.text",
            chat.language
        ).format(
            user=mention(user),
            warns=member.warns,
            max_warns=chat.warns_limit
        )
    )
