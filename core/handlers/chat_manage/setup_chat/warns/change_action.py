from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from sqlalchemy import update

from .....database import models
from ..... import translations, filters

from ..chat_state import get_chat_state


def register_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        change_action,
        lambda q: q.data == "change_warns_action",
        filters.MemberIsAdmin()
    )

    dp.register_callback_query_handler(
        choose_action,
        state=WarnsAction.choose
    )


class WarnsAction(StatesGroup):
    choose = State()


async def change_action(query: types.CallbackQuery, state: FSMContext):
    chat = models.Chat.from_dict((await get_chat_state(query.message.chat.id).get_data())["chat"])

    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=("✅" if chat.warns_action == "mute" else "") + "mute",
                    callback_data="set_warns_action mute"
                ),
                types.InlineKeyboardButton(
                    text=("✅" if chat.warns_action == "ban" else "") + "ban",
                    callback_data="set_warns_action ban"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=("✅" if chat.warns_action == "kick" else "") + "kick",
                    callback_data="set_warns_action kick"
                )
            ],
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

    await query.message.edit_text(
        text=translations.get_string(
            "settings.warns.action.text",
            chat.language
        ),
        reply_markup=markup
    )

    # noinspection PyTypeChecker
    await state.set_state(WarnsAction.choose)

    await query.answer("Success!")


async def choose_action(query: types.CallbackQuery):
    chat = models.Chat.from_dict((await get_chat_state(query.message.chat.id).get_data())["chat"])

    if chat.warns_action == query.data.split()[1]:
        return await query.answer(
            "This is current warns action of your chat"
        )

    async with query.bot.db() as session:
        await session.execute(
            update(
                models.Chat
            ).values(
                warns_action=query.data.split()[1]
            ).where(
                models.Chat.id == chat.id
            )
        )
        await session.commit()

    await query.bot.cache.refresh_chat(query.message.chat.id)

    chat.warns_action = query.data.split()[1]

    await get_chat_state(query.message.chat.id).update_data(
        {
            "chat": chat.to_dict()
        }
    )

    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=("✅" if chat.warns_action == "mute" else "") + "mute",
                    callback_data="set_warns_action mute"
                ),
                types.InlineKeyboardButton(
                    text=("✅" if chat.warns_action == "ban" else "") + "ban",
                    callback_data="set_warns_action ban"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=("✅" if chat.warns_action == "kick" else "") + "kick",
                    callback_data="set_warns_action kick"
                )
            ],
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

    await query.message.edit_reply_markup(
        reply_markup=markup
    )

    await query.answer("Success!")
