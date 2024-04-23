from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from ..... import translations, filters
from .....database import models


router = Router()


def get_keyboard(limit: int, action: str, language="en"):
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=translations.get_string(
                        "settings.warns.limit.label", language
                    ),
                    callback_data="change_warns_limit",
                ),
                types.InlineKeyboardButton(
                    text=str(limit), callback_data="change_warns_limit"
                ),
            ],
            [
                types.InlineKeyboardButton(
                    text=translations.get_string(
                        "settings.warns.action.label", language
                    ),
                    callback_data="change_warns_action",
                ),
                types.InlineKeyboardButton(
                    text=action, callback_data="change_warns_action"
                ),
            ],
            [
                types.InlineKeyboardButton(
                    text=translations.get_string(
                        "settings.warns.action_time.label", language
                    ),
                    callback_data="change_warns_action_time",
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=translations.get_string("settings.back-button", language),
                    callback_data="open_chat_settings",
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


@router.callback_query(
    F.data == "open_chat_warns_settings",
    filters.MemberIsAdmin(),
)
async def warns_settings(
    query: types.CallbackQuery, state: FSMContext, chat: models.Chat
):
    markup = get_keyboard(chat.warns_limit, chat.warns_action, chat.language)

    await query.message.edit_text(
        text=translations.get_string("settings.warns.text", chat.language),
        reply_markup=markup,
    )

    if await state.get_state() is not None:
        await state.set_state(None)
