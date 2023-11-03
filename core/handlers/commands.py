from aiogram import Dispatcher

from .. import translations, filters
from ..utils import types


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(
        get_commands, filters.Command(("commands", "команди"), prefixes=("!", "/"))
    )

    dp.register_callback_query_handler(
        get_commands,
        lambda q: q.data == "get_commands"
    )

    dp.register_callback_query_handler(
        get_usage, lambda q: q.data.startswith("get_command_usage")
    )


def chunker(iterable, length):
    for index in range(0, len(iterable), length):
        yield iterable[index : index + length]


async def get_commands(message: types.ExtendedMessage | types.ExtendedCallbackQuery):
    query = None
    if isinstance(message, types.CallbackQuery):
        query = message
        message = message.message
    chat = await message.bot.cache.get_chat(message.chat.id)

    commands = [
        (body, properties)
        for body, properties in translations.get("commands", chat.language).items()
        if body != "text"
    ]

    text = translations.get_string("commands.text", chat.language).format(
        commands="\n".join(
            f"› "
            + " / ".join(prefix + body for prefix in properties["prefixes"])
            + f" — {properties['desc']}"
            for body, properties in commands
        )
    )

    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=command, callback_data=f"get_command_usage {command}"
                )
                for command, *_ in chunk
            ]
            for chunk in chunker(
                list(filter(lambda x: x[1].get("usage", None) is not None, commands)),
                2,
            )
        ]
    )

    if not query:
        await message.reply(text=text, reply_markup=markup)
    else:
        await message.edit_text(text=text, reply_markup=markup)
        await query.answer()


async def get_usage(query: types.ExtendedCallbackQuery):
    chat = await query.bot.cache.get_chat(query.message.chat.id)
    body = query.data.split()[1].lower()

    commands = [
        (body.lower(), properties)
        for body, properties in translations.get("commands", chat.language).items()
        if body != "text"
    ]

    commands_found = list(filter(lambda x: x[0] == body, commands))

    if not len(commands_found) or "usage" not in commands_found[0][1]:
        return await query.answer("No usages found.")

    _, properties = commands_found[0]

    await query.message.edit_text(
        text=f"{body}:\n{properties['usage']}",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=translations.get_string(
                            "settings.back-button", chat.language
                        ),
                        callback_data="get_commands"
                    )
                ]
            ]
        ),
    )
    await query.answer()
