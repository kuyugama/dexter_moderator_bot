from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from sqlalchemy import update

from .....database import models
from ..... import translations, filters
from .....utils import strings

from ..chat_state import get_chat_state

from .warns_settings import get_keyboard


def register_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        change_limit,
        lambda q: q.data == "change_warns_limit",
        filters.MemberIsAdmin()
    )

    dp.register_message_handler(
        set_limit,
        state=WarnsLimit.input
    )


class WarnsLimit(StatesGroup):
    input = State()


async def change_limit(query: types.CallbackQuery, state: FSMContext):
    data = await get_chat_state(query.message.chat.id).get_data()

    chat = models.Chat.from_dict(data["chat"])

    sent = await query.message.edit_text(
        text=translations.get_string(
            "settings.warns.limit.text",
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
                        callback_data="open_chat_warns_settings"
                    )
                ]
            ]
        )
    )

    await get_chat_state(query.message.chat.id).update_data(
        {
            "sent_id": sent.message_id
        }
    )

    # noinspection PyTypeChecker
    await state.set_state(WarnsLimit.input)
    await query.answer("Success!")


async def set_limit(message: types.Message, state: FSMContext):
    data = await get_chat_state(message.chat.id).get_data()

    chat = models.Chat.from_dict(data["chat"])

    number = strings.to_int(message.text)

    if number == "nan" or number < 1:
        return await message.reply(
            text=translations.get_string(
                "settings.warns.limit.invalid_value",
                chat.language
            )
        )

    async with message.bot.db() as session:
        await session.execute(
            update(
                models.Chat
            ).values(
                warns_limit=number
            ).where(
                models.Chat.id == chat.id
            )
        )
        await session.commit()

    await message.bot.cache.refresh_chat(message.chat.id)

    chat.warns_limit = number

    await get_chat_state(message.chat.id).update_data(
        {
            "chat": chat.to_dict()
        }
    )

    await message.chat.delete_message(
        data["sent_id"]
    )

    await message.reply(
        text=translations.get_string(
            "settings.warns.text",
            chat.language
        ),
        reply_markup=get_keyboard(
            chat.warns_limit,
            chat.warns_action,
            chat.language
        )
    )

    await state.reset_state(False)
