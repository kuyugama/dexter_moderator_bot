from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from . import start, commands, chat_manage, show_bot_chats, mail

router = Router()

router.include_router(start.router)
router.include_router(chat_manage.router)
router.include_router(show_bot_chats.router)
router.include_router(mail.router)
router.include_router(commands.router)


@router.callback_query(F.data == "close_dialog")
async def close_callback_dialog(query: types.CallbackQuery, state: FSMContext):
    if await state.get_state() is not None:
        await state.clear()

    try:
        await query.message.delete()
    finally:
        await query.answer("Closed!")
