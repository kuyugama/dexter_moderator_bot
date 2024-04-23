from aiogram import types, Router, F
from aiogram.filters.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from sqlalchemy import update

from ..... import translations, filters, database
from .....database import models, Cache

router = Router()


class WarnsAction(StatesGroup):
    choose = State()


@router.callback_query(F.data == "change_warns_action", filters.MemberIsAdmin())
async def change_action(
    query: types.CallbackQuery, state: FSMContext, chat: models.Chat
):
    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=("✅" if chat.warns_action == "mute" else "") + "mute",
                    callback_data="set_warns_action mute",
                ),
                types.InlineKeyboardButton(
                    text=("✅" if chat.warns_action == "ban" else "") + "ban",
                    callback_data="set_warns_action ban",
                ),
            ],
            [
                types.InlineKeyboardButton(
                    text=("✅" if chat.warns_action == "kick" else "") + "kick",
                    callback_data="set_warns_action kick",
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=translations.get_string("settings.back-button", chat.language),
                    callback_data="open_chat_warns_settings",
                )
            ],
        ]
    )

    await query.message.edit_text(
        text=translations.get_string("settings.warns.action.text", chat.language),
        reply_markup=markup,
    )

    await state.set_state(WarnsAction.choose)
    await query.answer("Success!")


@router.callback_query(WarnsAction.choose)
async def choose(query: types.CallbackQuery, chat: models.Chat):
    warns_action = query.data.split()[1]
    if chat.warns_action == warns_action:
        return await query.answer("This is current warns action of your chat")

    async with database.session() as session:
        await session.execute(
            update(models.Chat)
            .values(warns_action=query.data.split()[1])
            .where(models.Chat.id == chat.id)
        )
        await session.commit()

    await Cache.instance.refresh_chat(query.message.chat.id)

    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=("✅" if warns_action == "mute" else "") + "mute",
                    callback_data="set_warns_action mute",
                ),
                types.InlineKeyboardButton(
                    text=("✅" if warns_action == "ban" else "") + "ban",
                    callback_data="set_warns_action ban",
                ),
            ],
            [
                types.InlineKeyboardButton(
                    text=("✅" if warns_action == "kick" else "") + "kick",
                    callback_data="set_warns_action kick",
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=translations.get_string("settings.back-button", chat.language),
                    callback_data="open_chat_warns_settings",
                )
            ],
        ]
    )

    await query.message.edit_reply_markup(reply_markup=markup)

    await query.answer("Success!")
