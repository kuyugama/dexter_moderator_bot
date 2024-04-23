from aiogram import types, Dispatcher, Router, F, exceptions
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StatesGroup, State
from sqlalchemy import update

from .....database import models, Cache
from ..... import translations, filters, database
from .....utils import strings

from .warns_settings import get_keyboard


router = Router()


class WarnsLimit(StatesGroup):
    input = State()


@router.callback_query(F.data == "change_warns_limit", filters.MemberIsAdmin())
async def entry(query: types.CallbackQuery, state: FSMContext, chat: models.Chat):

    sent = await query.message.edit_text(
        text=translations.get_string("settings.warns.limit.text", chat.language),
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=translations.get_string(
                            "settings.back-button", chat.language
                        ),
                        callback_data="open_chat_warns_settings",
                    )
                ]
            ]
        ),
    )

    await state.update_data(sent_id=sent.message_id)
    await state.set_state(WarnsLimit.input)
    await query.answer("Success!")


@router.message(WarnsLimit.input)
async def input_(message: types.Message, state: FSMContext, chat: models.Chat):
    number = strings.to_int(message.text)

    if number == "nan" or number < 1:
        return await message.reply(
            text=translations.get_string(
                "settings.warns.limit.invalid_value", chat.language
            )
        )

    async with database.session() as session:
        await session.execute(
            update(models.Chat)
            .values(warns_limit=number)
            .where(models.Chat.id == chat.id)
        )
        await session.commit()

    await Cache.instance.refresh_chat(message.chat.id)

    chat.warns_limit = number

    try:
        await message.chat.delete_message((await state.get_data()).get("sent_id"))
        await message.delete()
    except exceptions.TelegramBadRequest:
        pass

    await message.reply(
        text=translations.get_string("settings.warns.text", chat.language),
        reply_markup=get_keyboard(chat.warns_limit, chat.warns_action, chat.language),
        allow_sending_without_reply=True,
    )

    await state.set_state(None)
