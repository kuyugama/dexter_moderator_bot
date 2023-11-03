from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from sqlalchemy import update

from .... import translations
from ....database import models
from ....utils import strings

from .chat_settings import get_keyboard
from .... import filters


def register_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        change_welcome_message,
        lambda q: q.data == "change_welcome_message",
        filters.MemberIsAdmin()
    )

    dp.register_message_handler(
        set_welcome_message,
        state=WelcomeMessage.input
    )


class WelcomeMessage(StatesGroup):
    input = State()


async def change_welcome_message(query: types.CallbackQuery, state: FSMContext):
    chat = await query.bot.cache.get_chat(
        query.message.chat.id
    )

    sent = await query.message.edit_text(
        text=translations.get_string(
            "settings.welcome_message.text",
            chat.language
        ),
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=translations.get_string(
                            "settings.back-button",
                            chat.language
                        ),
                        callback_data="open_chat_settings"
                    )
                ]
            ]
        )
    )

    await state.update_data(
        {
            "sent_id": sent.message_id
        }
    )

    # noinspection PyTypeChecker
    await state.set_state(WelcomeMessage.input)


async def set_welcome_message(message: types.Message, state: FSMContext):
    chat = await message.bot.cache.get_chat(
        message.chat.id
    )

    if len(message.text) > 500:
        return

    async with message.bot.db() as session:
        await session.execute(
            update(
                models.Chat
            ).values(
                new_participant_greeting=message.text
            ).where(
                models.Chat.id == chat.id
            )
        )
        await session.commit()

    await message.bot.cache.refresh_chat(message.chat.id)

    await message.bot.delete_message(
        chat_id=message.chat.id,
        message_id=(await state.get_data())["sent_id"]
    )

    await message.reply(
        text=translations.get_string(
            "settings.info",
            chat.language
        ).format(
            name=message.chat.title,
            is_group=translations.get_string_by_list("values", chat.is_group, language=chat.language),
            chat_language=translations.get_languages()[chat.language],
            warns_limit=chat.warns_limit,
            warns_action=chat.warns_action,
            warns_action_time=(
                strings.beautify_time(
                    seconds=chat.warns_action_time,
                    language=chat.language
                )
                if chat.warns_action_time > 30
                else translations.get_string(
                    "values.forever",
                    chat.language
                )
            ),
            default_ban_time=(
                strings.beautify_time(
                    seconds=chat.default_ban_time,
                    language=chat.language
                )
                if chat.default_ban_time > 30
                else translations.get_string(
                    "values.forever",
                    chat.language
                )
            ),
            default_mute_time=(
                strings.beautify_time(
                    seconds=chat.default_mute_time,
                    language=chat.language
                )
                if chat.default_mute_time > 30
                else translations.get_string(
                    "values.forever",
                    chat.language
                )
            ),
            has_new_participants_greeting=translations.get_string_by_list(
                "values",
                chat.new_participant_greeting is not None,
                language=chat.language
            )
        ),
        reply_markup=get_keyboard(
            chat.language
        )
    )

    await state.reset_state()
