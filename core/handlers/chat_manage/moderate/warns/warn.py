from datetime import timedelta

from aiogram import Dispatcher, types
from sqlalchemy import update, delete

from ..... import translations, filters
from .....database import models
from .....utils import strings


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(
        warn,
        filters.Command(
            ("warn", "варн"),
            prefixes=("!", "/")
        ),
        filters.BotCanRestrict(),
        filters.MemberCanRestrict()
    )


async def warn(message: types.Message):
    chat = await message.bot.cache.get_chat(message.chat.id)

    mention_stack = strings.extract_user_mention(message.text)

    if not message.reply_to_message and not mention_stack:
        return await message.reply(
            text=translations.get_string(
                "warn.target_required",
                chat.language
            )
        )

    text = message.text

    if message.reply_to_message:
        victim = await message.chat.get_member(message.reply_to_message.from_user.id)

    else:
        mention, text = mention_stack

        if isinstance(mention, int):
            victim = await message.chat.get_member(mention)
        else:
            user_id = message.bot.cache.get(f"username:{mention}")

            if not user_id:
                return

            victim = await message.chat.get_member(user_id)

    if victim.is_chat_admin():
        return await message.reply(
            text=translations.get_string(
                "warn.victim_is_admin",
                chat.language
            )
        )

    if len(text.splitlines()[0].split()) < 2:
        count = 1
    else:
        count = strings.to_int(text.splitlines()[0].split(maxsplit=1)[1])

        if count == "nan" or count < 1:
            return await message.reply(
                text=translations.get_string(
                    "warn.incorrect_value",
                    chat.language
                )
            )

    reason = translations.get_string(
        "warn.no_reason",
        chat.language
    )

    if len(message.text.splitlines()) > 1:
        reason = "\n".join(message.text.splitlines()[1:])

    member = await message.bot.cache.get_member(victim.user.id, message.chat.id)

    if not member:
        return await message.reply(
            text=translations.get_string(
                "warn.member_not_exists",
                chat.language
            )
        )

    if member.warns + count < chat.warns_limit:
        async with message.bot.db() as session:
            await session.execute(
                update(
                    models.Member
                ).values(
                    warns=models.Member.warns + count
                ).where(
                    models.Member.user_id == member.user_id,
                    models.Member.chat_id == member.chat_id
                )
            )
            await session.commit()

        await message.bot.cache.refresh_member(
            victim.user.id,
            message.chat.id
        )

        return await message.reply(
            text=translations.get_string(
                "warn.success",
                chat.language
            ).format(
                victim=strings.get_mention(victim.user),
                warns=strings.beautify_represent(count, "warnings", chat.language, strings.beautify_number),
                reason=reason
            )
        )

    if chat.warns_action == "kick":
        await message.chat.unban(
            victim.user.id
        )

    elif chat.warns_action == "ban":
        await message.chat.kick(
            victim.user.id,
            until_date=timedelta(seconds=chat.warns_action_time)
        )

    else:
        await message.chat.restrict(
            victim.user.id,
            permissions=types.ChatPermissions(
                can_send_messages=False
            ),
            until_date=timedelta(seconds=chat.warns_action_time)
        )

    async with message.bot.db() as session:
        await session.execute(
            delete(
                models.Member
            ).where(
                models.Member.user_id == member.user_id,
                models.Member.chat_id == member.chat_id
            )
        )
        await session.commit()

    await message.bot.cache.refresh_member(
        message.reply_to_message.from_user.id,
        message.chat.id
    )

    await message.reply(
        text=translations.get_string(
            "warn.success_with_action",
            chat.language
        ).format(
            victim=strings.get_mention(victim.user),
            action=chat.warns_action,
            action_time=(
                (
                    strings.beautify_time(
                        seconds=chat.warns_action_time,
                        language=chat.language
                    )
                    if chat.warns_action_time > 30
                    else translations.get_string(
                        "values.forever",
                        chat.language
                    )
                )
                if chat.warns_action != "kick"
                else ""
            )

        )
    )
