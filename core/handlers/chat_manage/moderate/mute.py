from datetime import timedelta

from aiogram import types, Dispatcher
from m2h import Hum2Sec

from .... import translations, filters
from ....utils import strings
from ....utils.types import ExtendedMessage


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(
        mute_chat_member,
        filters.Command(
            ("mute", "мут"),
            prefixes=("!", "/")
        ),
        filters.BotCanRestrict(),
        filters.MemberCanRestrict() | filters.LocalBotAdmin()
    )


async def mute_chat_member(message: ExtendedMessage):
    chat = await message.bot.cache.get_chat(message.chat.id)

    mention_stack = strings.extract_user_mention(message.text)

    if not message.reply_to_message and not mention_stack:
        return await message.reply(
            text=translations.get_string(
                "mute.target_required",
                chat.language
            )
        )

    if message.reply_to_message and message.reply_to_message.sender_chat:
        return

    text = message.text

    if message.reply_to_message:
        victim = await message.chat.get_member(message.reply_to_message.from_user.id)

    else:
        mention, text = mention_stack

        if isinstance(mention, int):
            victim = await message.chat.get_member(mention)
        else:
            user_id = await message.bot.cache.get(f"username2id:{mention}")

            if not user_id:
                return

            victim = await message.chat.get_member(user_id)

    if victim.is_chat_admin():
        return await message.reply(
            text=translations.get_string(
                "mute.victim_is_admin",
                chat.language
            )
        )

    elif isinstance(victim, types.ChatMemberRestricted) and not victim.can_send_messages:
        return await message.reply(
            text=translations.get_string(
                "mute.victim_already_muted",
                chat.language
            )
        )

    if len(message.text.splitlines()[0].split()) > 1:
        parsed = Hum2Sec(text.splitlines()[0])
        time = parsed.seconds
        until_date = message.date + parsed.time_dlt

    else:
        time = chat.default_mute_time
        until_date = message.date + timedelta(seconds=chat.default_mute_time)

    cause = message.text.split("\n", maxsplit=1)[1:]

    if not len(cause):
        cause = translations.get_string(
            "mute.cause_not_specified",
            chat.language
        )
    else:
        cause = cause[0]

    await message.chat.restrict(
        user_id=victim.user.id,
        permissions=types.ChatPermissions(
            can_send_messages=False
        ),
        until_date=until_date
    )

    await message.reply(
        text=translations.get_string(
            "mute.success",
            chat.language
        ).format(
            victim=strings.get_mention(victim.user),
            reason=cause,
            by_admin=strings.get_mention(message.from_user),
            time=strings.beautify_time(seconds=time, language=chat.language),
            until_date=until_date.strftime("%d.%m.%y %H:%M:%S")
        )
    )
