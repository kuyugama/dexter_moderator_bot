from aiogram import types, Dispatcher, Router
from sqlalchemy import update

from .....middlewares import UsernameSaverMiddleware
from .....utils import strings
from .....database import models, Cache
from ..... import translations, filters, database

router = Router()


@router.message(
    filters.Command(("unwarn", "унварн"), prefixes=("!", "/")),
    filters.MemberCanRestrict(),
)
async def unwarn(message: types.Message, chat: models.Chat):
    cache = Cache.instance

    mention_stack = strings.extract_user_mention(message.text)

    if not message.reply_to_message and not mention_stack:
        return await message.reply(
            text=translations.get_string("unwarn.target_required", chat.language)
        )

    text = message.text

    if message.reply_to_message:
        victim = await message.chat.get_member(message.reply_to_message.from_user.id)

    else:
        mention, text = mention_stack

        if isinstance(mention, int):
            victim = await message.chat.get_member(mention)
        else:
            user_id = await cache.get(
                UsernameSaverMiddleware.username2id_template.format(username=mention)
            )

            if not user_id:
                return

            victim = await message.chat.get_member(user_id)

    if isinstance(victim, (types.ChatMemberAdministrator, types.ChatMemberOwner)):
        return await message.reply(
            text=translations.get_string("warn.victim_is_admin", chat.language)
        )

    member = await cache.get_member(victim.user.id, message.chat.id)

    if not member:
        return await message.reply(
            text=translations.get_string("unwarn.member_not_exist", chat.language)
        )

    if member.warns < 1:
        return await message.reply(
            text=translations.get_string("unwarn.no_warnings", chat.language)
        )

    count = 1

    if len(text.split()) > 1:
        count = strings.to_int(text.split(maxsplit=1)[1])

        if count == "nan":
            return await message.reply(
                text=translations.get_string("unwarn.incorrect_value", chat.language)
            )

    if count > member.warns:
        count = member.warns

    async with database.session() as session:
        await session.execute(
            update(models.Member)
            .values(warns=models.Member.warns - count)
            .where(
                models.Member.user_id == member.user_id,
                models.Member.chat_id == member.chat_id,
            )
        )
        await session.commit()

    await cache.refresh_member(victim.user.id, message.chat.id)

    await message.reply(
        text=translations.get_string_by_list(
            "unwarn", "success", language=chat.language
        ).format(
            warnings=(
                strings.beautify_represent(count, "warnings", chat.language)
                if count != member.warns
                else translations.get_string_by_list(
                    "values", "all", language=chat.language
                )
                + " "
                + strings.beautify_represent(9, "warnings", chat.language)
            )
        )
    )
