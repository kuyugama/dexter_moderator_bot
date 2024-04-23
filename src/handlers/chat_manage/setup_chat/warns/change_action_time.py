from aiogram import types, Router, F
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from m2h import Hum2Sec
from sqlalchemy import update

from .warns_settings import get_keyboard
from ..chat_state import get_chat_state
from ..... import translations, filters, database
from .....database import models, Cache
from .....utils import strings

router = Router()


class WarnsActionTime(StatesGroup):
    input = State()


@router.callback_query(F.data == "change_warns_action_time", filters.MemberIsAdmin())
async def change_action_time(
    query: types.CallbackQuery, state: FSMContext, chat: models.Chat
):
    sent = await query.message.edit_text(
        text=translations.get_string(
            "settings.warns.action_time.text", chat.language
        ).format(
            time=(
                strings.beautify_time(
                    seconds=chat.warns_action_time, language=chat.language
                )
                if chat.warns_action_time > 30
                else translations.get_string("values.forever", chat.language)
            )
        ),
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=translations.get_string(
                            "settings.back-button", chat.language
                        ),
                        callback_data="change_warns_settings",
                    )
                ]
            ]
        ),
    )

    await state.update_data(sent_id=sent.message_id)

    # noinspection PyTypeChecker
    await state.set_state(WarnsActionTime.input)


@router.message(WarnsActionTime.input)
async def set_action_time(message: types.Message, state: FSMContext, chat: models.Chat):
    parsed = Hum2Sec(message.text)

    seconds = parsed.seconds

    async with database.session() as session:
        await session.execute(
            update(models.Chat)
            .values(warns_action_time=seconds)
            .where(models.Chat.id == chat.id)
        )

        await session.commit()

    await Cache.instance.refresh_chat(message.chat.id)

    chat.warns_action_time = parsed.seconds

    markup = get_keyboard(chat.warns_limit, chat.warns_action, chat.language)

    await message.reply(
        text=translations.get_string("settings.warns.text", chat.language),
        reply_markup=markup,
    )

    await message.chat.delete_message(message_id=(await state.get_data())["sent_id"])

    await state.set_state(None)
