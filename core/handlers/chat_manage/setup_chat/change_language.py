from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from sqlalchemy import update

from ....database import models
from .... import translations, filters

from .chat_state import get_chat_state


def register_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        change_language,
        lambda q: q.data == "change_chat_language",
        filters.MemberIsAdmin()
    )

    dp.register_callback_query_handler(
        change_language,
        lambda q: q.data == "change_chat_language" and q.message.chat.type == "private"
    )

    dp.register_callback_query_handler(
        choose_language,
        state=Language.choose
    )


class Language(StatesGroup):
    choose = State()


async def change_language(query: types.CallbackQuery, state: FSMContext):
    data = await get_chat_state(query.message.chat.id).get_data()

    chat = models.Chat.from_dict(data["chat"])

    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=("✅" if chat.language == lang_code else "") + lang_name,
                    callback_data=f"set_chat_lang {lang_code}"
                )
                for lang_code, lang_name in translations.get_languages().items()
            ],
            [
                types.InlineKeyboardButton(
                    text=translations.get_string(
                        "settings.back-button",
                        language=chat.language
                    ),
                    callback_data="open_chat_settings"
                )
            ]
        ]
    )
    await query.message.edit_text(
        text=translations.get_string(
            "settings.language.available_languages",
            chat.language
        ).format(
            languages=', '.join(translations.get_languages().values())
        ),
        reply_markup=markup
    )

    # noinspection PyTypeChecker
    await state.set_state(Language.choose)
    await query.answer("Success!")


async def choose_language(query: types.CallbackQuery):
    data = await get_chat_state(query.message.chat.id).get_data()

    chat = models.Chat.from_dict(data["chat"])

    if query.data.split()[1] == chat.language:
        return await query.answer(
            "This is already language of your chat!"
        )

    async with query.bot.db() as session:
        await session.execute(
            update(
                models.Chat
            ).values(
                language=query.data.split()[1]
            ).where(
                models.Chat.id == chat.id
            )
        )
        await session.commit()

    await query.bot.cache.refresh_chat(query.message.chat.id)

    chat.language = query.data.split()[1]

    await get_chat_state(query.message.chat.id).update_data(
        {
            "chat": chat.to_dict()
        }
    )

    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=("✅" if chat.language == lang_code else "") + lang_name,
                    callback_data=f"set_chat_lang {lang_code}"
                )
                for lang_code, lang_name in translations.get_languages().items()
            ],
            [
                types.InlineKeyboardButton(
                    text=translations.get_string(
                        "settings.back-button",
                        language=chat.language
                    ),
                    callback_data="open_chat_settings"
                )
            ]
        ]
    )
    await query.message.edit_text(
        text=translations.get_string(
            "settings.language.available_languages",
            chat.language
        ).format(
            languages=', '.join(translations.get_languages().values())
        ),
        reply_markup=markup
    )
    await query.answer("Success!")
