from re import Pattern, compile

from aiogram.dispatcher.filters import Filter

from . import config
from . import translations
from .utils import types


class Command(Filter):
    def __init__(
        self,
        commands: [str],
        *arguments,
        prefixes: [str] = ("/",),
        no_args: bool = False,
    ):
        self.prefixes = prefixes if not prefixes == "" else [""]

        if not self.check_command_correctness(commands):
            raise TypeError("Command validation failed")

        if isinstance(commands, tuple):
            commands = list(commands)

        if not isinstance(commands, list):
            commands = [commands]

        for i, command in enumerate(commands):
            commands[i] = str(command).lower()

        self.no_args = no_args
        self.commands = commands
        arguments = list(arguments)
        for i, variants in enumerate(arguments):
            if isinstance(variants, tuple):
                arguments[i] = list(variants)
                continue
            if not isinstance(variants, list):
                arguments[i] = [variants]

        for variants in arguments:
            for i, variant in enumerate(variants):
                variants[i] = str(variant).lower()
        self.required_arguments = arguments

    @staticmethod
    def check_command_correctness(command: str) -> bool:
        if isinstance(command, (list, tuple)):
            return all(map(Command.check_command_correctness, command))
        elif isinstance(command, str) and len(command) > 0:
            command = command.lower()
            if "\n" in command or " " in command:
                return False
            return True
        return False

    def check_arguments(self, args):
        if self.no_args:
            return len(args) < 1
        if len(self.required_arguments) < 1:

            return True
        if len(self.required_arguments) > len(args):
            return False
        for equaled_argument, variants in zip(args, self.required_arguments):
            if all(
                map(
                    lambda x: x[0] != x[1],
                    zip([equaled_argument] * len(variants), variants),
                )
            ):
                return False
        return True

    async def check(self, message: types.Message):
        if not any([message.text.startswith(prefix) for prefix in self.prefixes]):
            return False
        for prefix in self.prefixes:
            if not message.text.lower().startswith(prefix):
                continue
            text = message.text[len(prefix) :].lower()
            mention = "@" + (await message.bot.me).username.lower()
            if len(text.split()) < 1:
                return False
            for command in self.commands:
                if text.startswith(command):
                    message.command_body = command
                    text_after_command = text[len(command) :]

                    if text_after_command.startswith("@"):
                        if text_after_command.startswith(mention):
                            text_after_command = text_after_command[len(mention) :]
                        else:
                            return False

                    if len(text_after_command) == 0 or text_after_command[0] in (
                        " ",
                        "\n",
                    ):
                        arguments = text_after_command[1:]
                    else:
                        continue
                    arguments = arguments.split(" ") if len(arguments) else []

                    message.args = arguments
                    return self.check_arguments(message.args)
        return False


class NotAnonymous(Filter):
    @staticmethod
    async def check(message: types.Message):
        return not message.sender_chat


class MemberIsAdmin(Filter):
    @staticmethod
    async def check(obj: types.ExtendedMessage | types.ExtendedCallbackQuery):
        if isinstance(obj, types.Message):
            chat = obj.chat

            if obj.sender_chat:
                return obj.sender_chat.id == chat.id
        elif isinstance(obj, types.CallbackQuery) and obj.message:
            chat = obj.message.chat
        else:
            return

        cache = obj.bot.cache

        chat_administrators = await cache.get(f"chat_administrators:{chat.id}")

        if not chat_administrators:
            chat_administrators = [
                dict(id=admin.user.id, can_restrict=admin.can_restrict_members) for admin in await chat.get_administrators()
            ]
            await cache.set(f"chat_administrators:{chat.id}", chat_administrators, 600)

        return obj.from_user.id in list(map(lambda x: x["id"], chat_administrators))


class MemberCanRestrict(Filter):
    @staticmethod
    async def check(obj: types.ExtendedMessage | types.ExtendedCallbackQuery):

        if isinstance(obj, types.Message):
            chat = obj.chat

            if obj.sender_chat:
                return obj.sender_chat.id == chat.id
        elif isinstance(obj, types.CallbackQuery) and obj.message:
            chat = obj.message.chat
        else:
            return

        cache = obj.bot.cache

        chat_administrators = await cache.get(f"chat_administrators:{chat.id}")

        if not chat_administrators:
            chat_administrators = [
                dict(id=admin.user.id, can_restrict=admin.can_restrict_members) for admin in await chat.get_administrators()
            ]
            await cache.set(f"chat_administrators:{chat.id}", chat_administrators, 600)

        user_admin: list[dict] = list(filter(lambda x: x["id"] == obj.from_user.id, chat_administrators))

        if not user_admin:
            return False

        user_admin: dict = user_admin[0]

        return user_admin["can_restrict"]


class BotIsAdmin(Filter):
    async def check(self, message: types.ExtendedMessage, *args) -> bool:
        cache = message.bot.cache

        chat_bot = await cache.get(f"chat_bot:{message.chat.id}")

        if not chat_bot:
            chat_bot = (await message.chat.get_member(message.bot.id)).to_python()
            await cache.set(f"chat_bot:{message.chat.id}", chat_bot, 600)

        statement = chat_bot.get("status") in ("administrator", "creator")

        if not statement:
            chat = await cache.get_chat(message.chat.id)
            await message.reply(
                text=translations.get_string(
                    "bot_admin_required",
                    chat.language
                )
            )

        return statement


class BotCanRestrict(Filter):
    async def check(self, message: types.ExtendedMessage) -> bool:
        cache = message.bot.cache

        chat_bot = await cache.get(f"chat_bot:{message.chat.id}")

        if not chat_bot:
            chat_bot = (await message.chat.get_member(message.bot.id)).to_python()
            await cache.set(f"chat_bot:{message.chat.id}", chat_bot, 600)

        statement = chat_bot.get("status") in ("administrator", "creator") and chat_bot.get(
            "can_restrict_members"
        )

        if not statement:
            chat = await cache.get_chat(message.chat.id)
            await message.reply(
                text=translations.get_string(
                    "bot_cant_restrict_member",
                    chat.language
                )
            )

        return statement


class RegExp(Filter):
    def __init__(self, pattern, flags=0):
        if isinstance(pattern, str):
            pattern = compile(pattern, flags)
        elif not isinstance(pattern, Pattern):
            raise ValueError("pattern type not supported")
        self.pattern = pattern

    async def check(self, message: types.Message):
        message.matches = list(self.pattern.finditer(message.text)) or None
        return message.matches is not None


class LocalBotAdmin(Filter):
    async def check(self, message: types.Message):
        return message.from_id in config.administrators
