from aiogram import Dispatcher, types, Router, filters as aio_filters

from .... import translations
from .... import filters
from src.utils import strings
from ....database import models, Cache
from ....middlewares import UsernameSaverMiddleware


router = Router()


@router.message(
    filters.Command(("кік", "kick"), prefixes=("!", "/")),
    filters.BotCanRestrict(),
    aio_filters.or_f(filters.MemberCanRestrict(), filters.LocalBotAdmin()),
)
async def kick_member(message: types.Message, chat: models.Chat):
    cache = Cache.instance
    mention_stack = strings.extract_user_mention(message.text)

    if not message.reply_to_message and not mention_stack:
        return await message.reply(
            text=translations.get_string("kick.target_required", chat.language)
        )

    reason = translations.get_string("kick.no_reason", chat.language)

    if len(message.text.split()) > 1:
        reason = message.text.split(maxsplit=1)[1]

    if message.reply_to_message.sender_chat:
        return

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

    if victim.is_chat_admin():
        return await message.reply(
            text=translations.get_string("kick.victim_is_admin", chat.language)
        )

    if victim.status in ("kicked", "left"):
        return await message.reply(
            text=translations.get_string("kick.victim_already_kicked", chat.language)
        )

    await message.chat.unban(victim.user.id)

    await message.reply(
        text=translations.get_string("kick.success", chat.language).format(
            victim=strings.get_mention(victim.user),
            reason=reason,
            by_admin=strings.get_mention(message.from_user),
        )
    )
