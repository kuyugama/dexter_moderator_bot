from aiogram import types, Dispatcher, F, Router, filters as aio_filters
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StatesGroup, State
from sqlalchemy import update

from ....database import models, Cache
from .... import translations, filters, database

from .chat_state import get_chat_state


router = Router()


class Language(StatesGroup):
    choose = State()


@router.callback_query(
    F.data == "change_chat_language",
    aio_filters.or_f(filters.MemberIsAdmin(), F.message.chat.type == "private"),
)
async def change_language(query: types.CallbackQuery, state: FSMContext):
    data = await get_chat_state(query.message.chat.id, query.bot.id, state).get_data()

    chat = models.Chat.from_dict(data["chat"])

    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=("✅" if chat.language == lang_code else "") + lang_name,
                    callback_data=f"set_chat_lang {lang_code}",
                )
                for lang_code, lang_name in translations.get_languages().items()
            ],
            [
                types.InlineKeyboardButton(
                    text=translations.get_string(
                        "settings.back-button", language=chat.language
                    ),
                    callback_data="open_chat_settings",
                )
            ],
        ]
    )
    await query.message.edit_text(
        text=translations.get_string(
            "settings.language.available_languages", chat.language
        ).format(languages=", ".join(translations.get_languages().values())),
        reply_markup=markup,
    )

    # noinspection PyTypeChecker
    await state.set_state(Language.choose)
    await query.answer("Success!")


@router.callback_query(Language.choose)
async def choose_language(query: types.CallbackQuery, state):
    cache = Cache.instance
    chat_state = get_chat_state(query.message.chat.id, query.bot.id, state)
    data = await chat_state.get_data()

    chat = models.Chat.from_dict(data["chat"])

    if query.data.split()[1] == chat.language:
        return await query.answer("This is already language of your chat!")

    async with database.session() as session:
        await session.execute(
            update(models.Chat)
            .values(language=query.data.split()[1])
            .where(models.Chat.id == chat.id)
        )
        await session.commit()

    await cache.refresh_chat(query.message.chat.id)

    chat.language = query.data.split()[1]

    await chat_state.update_data({"chat": chat.to_dict()})

    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=("✅" if chat.language == lang_code else "") + lang_name,
                    callback_data=f"set_chat_lang {lang_code}",
                )
                for lang_code, lang_name in translations.get_languages().items()
            ],
            [
                types.InlineKeyboardButton(
                    text=translations.get_string(
                        "settings.back-button", language=chat.language
                    ),
                    callback_data="open_chat_settings",
                )
            ],
        ]
    )
    await query.message.edit_text(
        text=translations.get_string(
            "settings.language.available_languages", chat.language
        ).format(languages=", ".join(translations.get_languages().values())),
        reply_markup=markup,
    )
    await query.answer("Success!")
