from aiogram import Router, filters as aio_filters, types

from ....database import models, Cache
from ....middlewares import UsernameSaverMiddleware
from ....utils import strings
from .... import filters, translations


router = Router()


@router.message(
    filters.Command(("pardon", "amplify", "unban", "пардон"), prefixes=("!", "/")),
    filters.BotCanRestrict(),
    aio_filters.or_f(filters.MemberCanRestrict(), filters.LocalBotAdmin()),
)
async def pardon_member(message: types.Message, chat: models.Chat):
    cache = Cache.instance

    mention_stack = strings.extract_user_mention(message.text)

    if not message.reply_to_message and not mention_stack:
        return await message.reply(
            text=translations.get_string("pardon.target_required", chat.language)
        )

    if message.reply_to_message:
        victim = await message.chat.get_member(message.reply_to_message.from_user.id)

    else:
        mention, _ = mention_stack

        if isinstance(mention, int):
            victim = await message.chat.get_member(mention)
        else:
            user_id = await cache.get(
                UsernameSaverMiddleware.username2id_template.format(username=mention)
            )

            if not user_id:
                return

            victim = await message.chat.get_member(user_id)

    if await cache.get(f"ban_request:{message.chat.id}:{victim.user.id}"):
        await cache.remove(f"ban_request:{message.chat.id}:{victim.user.id}")

        return await message.reply(
            text=translations.get_string(
                "pardon.all_restrictions_canceled", chat.language
            )
        )

    if victim.status == "kicked":
        await message.chat.unban(victim.user.id)

        return await message.reply(
            text=translations.get_string(
                "pardon.all_restrictions_canceled", chat.language
            )
        )

    if victim.status == "restricted":
        await message.chat.restrict(
            victim.user.id,
            types.ChatPermissions(
                can_send_messages=True,
                can_pin_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_send_polls=True,
                can_change_info=True,
                can_invite_users=True,
                can_add_web_page_previews=True,
            ),
        )

        return await message.reply(
            text=translations.get_string(
                "pardon.all_restrictions_canceled", chat.language
            )
        )

    await message.reply(
        text=translations.get_string("pardon.no_punishment", chat.language)
    )
