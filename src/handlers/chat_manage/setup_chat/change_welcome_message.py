from aiogram import types, Router, F
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy import update

from .chat_settings import get_keyboard
from .... import filters
from .... import translations, database
from ....database import models, Cache
from ....utils import strings

router = Router()


class WelcomeMessage(StatesGroup):
    input = State()


@router.callback_query(F.data == "change_welcome_message", filters.MemberIsAdmin())
async def change_welcome_message(query: types.CallbackQuery, state: FSMContext):
    chat = await Cache.instance.get_chat(query.message.chat.id)

    sent = await query.message.edit_text(
        text=translations.get_string("settings.welcome_message.text", chat.language),
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=translations.get_string(
                            "settings.back-button", chat.language
                        ),
                        callback_data="open_chat_settings",
                    )
                ]
            ]
        ),
    )

    await state.update_data({"sent_id": sent.message_id})

    # noinspection PyTypeChecker
    await state.set_state(WelcomeMessage.input)


@router.message(WelcomeMessage.input)
async def set_welcome_message(
    message: types.Message, chat: models.Chat, state: FSMContext
):
    cache = Cache.instance
    if len(message.text) > 500:
        return

    async with database.session() as session:
        await session.execute(
            update(models.Chat)
            .values(new_participant_greeting=message.text)
            .where(models.Chat.id == chat.id)
        )
        await session.commit()

    await cache.refresh_chat(message.chat.id)

    await message.bot.delete_message(
        chat_id=message.chat.id, message_id=(await state.get_data())["sent_id"]
    )

    await message.reply(
        text=translations.get_string("settings.info", chat.language).format(
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
        ),
        reply_markup=get_keyboard(chat.language),
    )

    await state.set_state(None)
