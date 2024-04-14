import asyncio
from datetime import timedelta

from aiogram import types, Dispatcher
from m2h import Hum2Sec

from .... import filters, translations
from ....middlewares import UsernameSaverMiddleware
from ....utils import strings, types


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(
        ban_chat_member,
        filters.Command(("ban", "бан"), prefixes=("!", "/")),
        filters.BotCanRestrict(),
        filters.MemberCanRestrict(),
    )


async def ban_chat_member(message: types.ExtendedMessage):
    chat = await message.bot.cache.get_chat(message.chat.id)

    message_author = message.from_user or message.sender_chat

    mention_stack = strings.extract_user_mention(message.text)

    if not message.reply_to_message and not mention_stack:
        return await message.reply(
            text=translations.get_string("ban.target_required", chat.language)
        )

    if len(message.text.splitlines()[0].split()) > 1:
        text = message.text
        if mention_stack:
            text = mention_stack[1]
        parsed = Hum2Sec(text.splitlines()[0])
        time = parsed.seconds
        until_date = message.date + parsed.time_dlt

    else:
        time = chat.default_mute_time
        until_date = message.date + timedelta(seconds=chat.default_mute_time)

    reason = message.text.split("\n", maxsplit=1)[1:]
    if not len(reason):
        reason = translations.get_string("ban.no_reason", chat.language)
    else:
        reason = reason[0]

    if message.reply_to_message and message.reply_to_message.sender_chat:
        if message.reply_to_message.sender_chat.id == chat.id:
            return await message.reply(
                text=translations.get_string("ban.victim_is_admin", chat.language)
            )

        await message.chat.ban_sender_chat(message.reply_to_message.sender_chat.id)

        return await message.reply(
            text=translations.get_string("ban.success", chat.language).format(
                reason=reason,
                victim=strings.get_mention(message.reply_to_message.sender_chat),
                by_admin=strings.get_mention(message_author),
                time=strings.beautify_time(seconds=time, language=chat.language),
                until_date=until_date.strftime("%d.%m.%y %H:%M:%S"),
            )
        )

    if message.reply_to_message:
        victim = await message.chat.get_member(message.reply_to_message.from_user.id)

    else:
        mention, _ = mention_stack

        if isinstance(mention, int):
            victim = await message.chat.get_member(mention)
        else:
            user_id = message.bot.cache.get(
                UsernameSaverMiddleware.username2id_template.format(username=mention)
            )

            if not user_id:
                return

            victim = await message.chat.get_member(user_id)

    if victim.is_chat_admin():
        return await message.reply(
            text=translations.get_string("ban.victim_is_admin", chat.language)
        )

    elif isinstance(victim, types.ChatMemberBanned):
        return await message.reply(
            text=translations.get_string("ban.victim_already_banned", chat.language)
        )

    await message.chat.restrict(
        victim.user.id,
        permissions=types.ChatPermissions(can_send_messages=False),
        until_date=timedelta(minutes=7),
    )

    await message.bot.cache.set(
        f"ban_request:{message.chat.id}:{victim.user.id}", 1, 420
    )

    notification = await message.reply(
        text=translations.get_string("ban.notification", chat.language).format(
            victim=strings.get_mention(victim.user),
            by_admin=strings.get_mention(message_author),
            reason=reason,
        )
    )

    await asyncio.sleep(300)

    if not (
        await message.bot.cache.get(f"ban_request:{message.chat.id}:{victim.user.id}")
    ):
        return

    await message.bot.cache.remove(f"ban_request:{message.chat.id}:{victim.user.id}")

    await message.chat.kick(
        victim.user.id, until_date=until_date + timedelta(minutes=5)
    )

    await message.reply(
        text=translations.get_string("ban.success", chat.language).format(
            victim=strings.get_mention(victim.user),
            reason=reason,
            by_admin=strings.get_mention(message_author),
            time=strings.beautify_time(seconds=time, language=chat.language),
            until_date=until_date.strftime("%d.%m.%y %H:%M:%S"),
        )
    )

    await notification.delete()
