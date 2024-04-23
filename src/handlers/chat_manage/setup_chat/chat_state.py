from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey


def get_chat_state(chat: int, bot: int, state: FSMContext) -> FSMContext:
    return FSMContext(state.storage, StorageKey(bot, chat, chat))
