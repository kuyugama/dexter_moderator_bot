from aiogram import types, Router
from aiogram.filters import CommandStart

from .. import translations
from ..database import Cache

router = Router()


@router.message(CommandStart())
async def start(message: types.Message):
    chat = await Cache.instance.get_chat(message.chat.id)
    if message.chat.type == "private":
        return await message.reply(
            text=translations.get_string("start.private", chat.language),
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(
                            text=translations.get_string(
                                "start.private-button", chat.language
                            ),
                            url=f"t.me/{(await message.bot.me()).username}?startgroup=true",
                        )
                    ]
                ]
            ),
        )

    if message.text == "/start true":
        return await message.reply(
            text=translations.get_string("start.group_when_added", chat.language)
        )

    await message.reply(text=translations.get_string("start.group", chat.language))
