from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext

from .. import filters
from . import (
    start,
    commands,
    chat_manage,
    show_bot_chats,
    mail
)


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(
        start.start,
        filters.Command(
            "start"
        )
    )

    dp.register_callback_query_handler(
        close_callback_dialog,
        lambda q: q.data == "close_dialog",
        state="*"
    )

    commands.register_handlers(dp)

    chat_manage.register_handlers(dp)

    show_bot_chats.register_handlers(dp)

    mail.register_handlers(dp)


async def close_callback_dialog(query: types.CallbackQuery, state: FSMContext):
    if await state.get_state() is not None:
        await state.finish()

    try:
        await query.message.delete()
    finally:
        await query.answer("Closed!")
