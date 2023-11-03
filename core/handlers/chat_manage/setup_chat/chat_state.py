from aiogram import Dispatcher


def get_chat_state(chat: int):
    return Dispatcher.get_current().current_state(chat=chat, user=chat)
