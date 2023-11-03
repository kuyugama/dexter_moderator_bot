from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from m2h import Hum2Sec
from sqlalchemy import update

from ....database import models
from ....utils import strings
from .... import translations, filters

from .chat_state import get_chat_state
from .chat_settings import get_keyboard


def register_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        change_default_mute_duration,
        lambda q: q.data == "change_default_mute_time",
        filters.MemberIsAdmin()
    )

    dp.register_message_handler(
        set_default_mute_duration,
        state=DefaultMuteDuration.input
    )


class DefaultMuteDuration(StatesGroup):
    input = State()


async def change_default_mute_duration(query: types.CallbackQuery, state: FSMContext):
    chat_state = get_chat_state(query.message.chat.id)
    chat_data = await chat_state.get_data()

    chat = models.Chat.from_dict(chat_data["chat"])

    sent = await query.message.edit_text(
        text=translations.get_string(
            "settings.default_mute_time.text",
            chat.language
        ).format(
            time=(
                strings.beautify_time(
                    seconds=chat.default_mute_time,
                    language=chat.language
                )
                if chat.default_mute_time > 30
                else translations.get_string(
                    "values.forever",
                    chat.language
                )
            )
        ),
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        translations.get_string(
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
    await state.set_state(DefaultMuteDuration.input)


async def set_default_mute_duration(message: types.Message, state: FSMContext):
    chat_state = get_chat_state(message.chat.id)
    chat_data = await chat_state.get_data()

    chat = models.Chat.from_dict(chat_data["chat"])
    parsed = Hum2Sec(message.text)

    async with message.bot.db() as session:
        await session.execute(
            update(
                models.Chat
            ).values(
                default_mute_time=parsed.seconds
            ).where(
                models.Chat.id == chat.id
            )
        )
        await session.commit()

    chat.default_mute_time = parsed.seconds

    await chat_state.update_data(
        {
            "chat": chat.to_dict()
        }
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

    await message.bot.cache.refresh_chat(chat.id)

    await message.bot.delete_message(
        chat_id=message.chat.id,
        message_id=(await state.get_data())["sent_id"]
    )

    await state.reset_state(False)
