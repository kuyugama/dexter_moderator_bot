from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from .... import translations, filters
from ....utils import strings
from ....database import models
from .chat_state import get_chat_state


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(
        chat_settings,
        filters.Command("settings", no_args=True),
        filters.NotAnonymous(),
        filters.MemberIsAdmin()
    )

    dp.register_message_handler(
        chat_settings,
        filters.Command("settings", no_args=True),
        lambda m: m.chat.type == "private",
    )

    dp.register_callback_query_handler(
        back_to_chat_settings,
        lambda q: q.data == "open_chat_settings",
        filters.MemberIsAdmin(),
        state="*",
    )

    dp.register_callback_query_handler(
        back_to_chat_settings,
        lambda q: q.data == "open_chat_settings" and q.message.chat.type == "private",
        state="*",
    )


def get_keyboard(language="en"):
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=translations.get_string("settings.language.label", language),
                    callback_data="change_chat_language",
                ),
                types.InlineKeyboardButton(
                    text=translations.get_languages()[language],
                    callback_data="change_chat_language",
                ),
            ],
            [
                types.InlineKeyboardButton(
                    text=translations.get_string("settings.warns.label", language),
                    callback_data="open_chat_warns_settings",
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=translations.get_string(
                        "settings.default_ban_time.label", language
                    ),
                    callback_data="change_default_ban_time",
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=translations.get_string(
                        "settings.default_mute_time.label", language
                    ),
                    callback_data="change_default_mute_time",
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=translations.get_string(
                        "settings.welcome_message.label", language
                    ),
                    callback_data="change_welcome_message",
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=translations.get_string("settings.close_dialog", language),
                    callback_data="close_dialog",
                )
            ],
        ]
    )


def get_private_keyboard(language: str = "en") -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=translations.get_string("settings.language.label", language),
                    callback_data="change_chat_language",
                ),
                types.InlineKeyboardButton(
                    text=translations.get_languages()[language],
                    callback_data="change_chat_language",
                ),
            ],
            [
                types.InlineKeyboardButton(
                    text=translations.get_string("settings.close_dialog", language),
                    callback_data="close_dialog",
                )
            ],
        ]
    )


async def chat_settings(message: types.Message):
    # noinspection PyUnresolvedReferences
    chat: models.Chat = await message.bot.cache.get_chat(message.chat.id)

    if not chat:
        return await message.reply(
            text="We have a problem. "
            "Settings of group is not found in database. "
            "Write about this to @youngtitanium"
        )

    if message.chat.type != "private":
        markup = get_keyboard(chat.language)
        text = translations.get_string("settings.info", chat.language).format(
            name=message.chat.title,
            is_group=translations.get_string_by_list(
                "values", chat.is_group, language=chat.language
            ),
            chat_language=translations.get_languages()[chat.language],
            warns_limit=chat.warns_limit,
            warns_action=chat.warns_action,
            warns_action_time=(
                strings.beautify_time(
                    seconds=chat.warns_action_time, language=chat.language
                )
                if chat.warns_action_time > 30
                else translations.get_string("values.forever", chat.language)
            ),
            default_ban_time=(
                strings.beautify_time(
                    seconds=chat.default_ban_time, language=chat.language
                )
                if chat.default_ban_time > 30
                else translations.get_string("values.forever", chat.language)
            ),
            default_mute_time=(
                strings.beautify_time(
                    seconds=chat.default_mute_time, language=chat.language
                )
                if chat.default_mute_time > 30
                else translations.get_string("values.forever", chat.language)
            ),
            has_new_participants_greeting=translations.get_string_by_list(
                "values",
                chat.new_participant_greeting is not None,
                language=chat.language,
            ),
        )
    else:
        markup = get_private_keyboard(chat.language)
        text = translations.get_string("settings.private_info", chat.language).format(
            name=message.from_user.full_name,
            chat_language=translations.get_languages()[chat.language],
        )

    await message.reply(text=text, reply_markup=markup)

    await get_chat_state(message.chat.id).update_data({"chat": chat.to_dict()})


async def back_to_chat_settings(query: types.CallbackQuery, state: FSMContext):
    data = await get_chat_state(query.message.chat.id).get_data()

    if "chat" in data:
        chat = models.Chat.from_dict(data["chat"])
    else:
        chat = query.bot.cache.get_chat(query.message.chat.id)

        await get_chat_state(query.message.chat.id).update_data(
            {"chat": chat.to_dict()}
        )

    if query.message.chat.type != "private":
        markup = get_keyboard(chat.language)
        text = translations.get_string("settings.info", chat.language).format(
            name=query.message.chat.title,
            is_group=translations.get_string_by_list(
                "values", chat.is_group, language=chat.language
            ),
            chat_language=translations.get_languages()[chat.language],
            warns_limit=chat.warns_limit,
            warns_action=chat.warns_action,
            warns_action_time=(
                strings.beautify_time(
                    seconds=chat.warns_action_time, language=chat.language
                )
                if chat.warns_action_time > 30
                else translations.get_string("values.forever", chat.language)
            ),
            default_ban_time=(
                strings.beautify_time(
                    seconds=chat.default_ban_time, language=chat.language
                )
                if chat.default_ban_time > 30
                else translations.get_string("values.forever", chat.language)
            ),
            default_mute_time=(
                strings.beautify_time(
                    seconds=chat.default_mute_time, language=chat.language
                )
                if chat.default_mute_time > 30
                else translations.get_string("values.forever", chat.language)
            ),
            has_new_participants_greeting=translations.get_string_by_list(
                "values",
                chat.new_participant_greeting is not None,
                language=chat.language,
            ),
        )
    else:
        markup = get_private_keyboard(chat.language)
        text = translations.get_string("settings.private_info", chat.language).format(
            name=query.from_user.full_name,
            chat_language=translations.get_languages()[chat.language],
        )

    await query.message.edit_text(text=text, reply_markup=markup)

    await state.reset_state(False)
    await query.answer("Success!")
