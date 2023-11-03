from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from m2h import Hum2Sec
from sqlalchemy import update

from .....database import models
from .....utils import strings
from ..... import translations, filters

from ..chat_state import get_chat_state
from .warns_settings import get_keyboard


def register_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        change_action_time,
        lambda q: q.data == "change_warns_action_time",
        filters.MemberIsAdmin()
    )

    dp.register_message_handler(
        set_action_time,
        state=WarnsActionTime.input
    )


class WarnsActionTime(StatesGroup):
    input = State()


async def change_action_time(query: types.CallbackQuery, state: FSMContext):
    chat = models.Chat.from_dict((await get_chat_state(query.message.chat.id).get_data())["chat"])

    sent = await query.message.edit_text(
        text=translations.get_string(
            "settings.warns.action_time.text",
            chat.language
        ).format(
            time=(
                strings.beautify_time(
                    seconds=chat.warns_action_time,
                    language=chat.language
                )
                if chat.warns_action_time > 30
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
                        text=translations.get_string(
                            "settings.back-button",
                            chat.language
                        ),
                        callback_data="change_warns_settings"
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
    await state.set_state(WarnsActionTime.input)


async def set_action_time(message: types.Message, state: FSMContext):
    chat = models.Chat.from_dict((await get_chat_state(message.chat.id).get_data())["chat"])
    parsed = Hum2Sec(message.text)

    seconds = parsed.seconds

    async with message.bot.db() as session:
        await session.execute(
            update(
                models.Chat
            ).values(
                warns_action_time=seconds
            ).where(
                models.Chat.id == chat.id
            )
        )

        await session.commit()

    await message.bot.cache.refresh_chat(message.chat.id)

    chat.warns_action_time = parsed.seconds

    await get_chat_state(message.chat.id).update_data(
        {
            "chat": chat.to_dict()
        }
    )

    markup = get_keyboard(
        chat.warns_limit,
        chat.warns_action,
        chat.language
    )

    await message.reply(
        text=translations.get_string(
            "settings.warns.text",
            chat.language
        ),
        reply_markup=markup
    )

    await message.bot.delete_message(
        chat_id=message.chat.id,
        message_id=(await state.get_data())["sent_id"]
    )

    await state.reset_state(False)
