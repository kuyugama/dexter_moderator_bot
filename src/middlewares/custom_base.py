import types
from types import UnionType
from typing import Callable, Any, Awaitable, cast, TypedDict
import inspect

from aiogram import BaseMiddleware, Router
from aiogram.dispatcher.event.telegram import TelegramEventObserver
from aiogram.types import TelegramObject, ChatMemberUpdated

EVENT_HANDLER_KEY = "--event--"


class Event(TypedDict):
    event_type: tuple[type[TelegramObject]]
    data_required: bool


class ChatMember(ChatMemberUpdated):
    pass


class MyChatMember(ChatMemberUpdated):
    pass


def event(function: types.FunctionType):
    signature = inspect.signature(function)
    params = list(signature.parameters.values())

    data_required = len(params) == 3

    if params[0].name == "self" and "." not in function.__qualname__:
        raise ValueError("Not class member functions is not supported")

    event_type = params[1].annotation

    if isinstance(event_type, UnionType):
        event_types = event_type.__args__
    else:
        event_types = (event_type,)

    for event_type in event_types:
        if event_type is ChatMemberUpdated:
            raise ValueError(
                f"Method {function.__name__} uses aiogram.types.ChatMemberUpdated for event handler recognition, "
                f"but its not supported because Telegram have two different updates that "
                f"match one object and this causes confusing which update to handle. "
                f"So for deal this problem use the ChatMember and MyChatMember from this awesome module"
            )

    setattr(
        function,
        EVENT_HANDLER_KEY,
        Event(event_type=event_types, data_required=data_required),
    )

    return function


class CustomBaseMiddleware(BaseMiddleware):
    """
    Custom base middleware that MaGiCaLlY handles events

    Note: for ChatMemberUpdated use ChatMember and MyChatMember classes from this module

    example: ::

        class HelloWorldMiddleware(CustomBaseMiddleware):
            @event
            async def message(self, message: types.Message):
                print(f"Hello world by {message.from_user.first_name}!")
        ...
        # Registering it, so it will handle all message events(after filters)
        HelloWorldMiddleware().register(router)
        # Registering it before filters
        HelloWorldMiddleware().register(router, outer=True)
    """

    handlers_type = dict[
        type[TelegramObject],
        tuple[
            bool,
            Callable[[object, TelegramObject, dict[str, Any]], Awaitable[Any]]
            | Callable[[object, TelegramObject], Awaitable[Any]],
        ],
    ]

    _handlers: handlers_type

    def __init_subclass__(cls, **kwargs):
        cls._handlers = {}

        for method in cls.__dict__.values():
            if not isinstance(method, types.FunctionType):
                continue

            event_details = cast(Event, getattr(method, EVENT_HANDLER_KEY, None))

            if event_details is None:
                continue

            for event_type in event_details["event_type"]:
                cls._handlers[event_type] = event_details["data_required"], method

    @staticmethod
    def pascal_case_to_snake_case(s: str):
        return s[:1].lower() + "".join(
            char if char.islower() else "_" + char.lower() for char in s[1:]
        )

    def install_middleware(self, observer: TelegramEventObserver, outer: bool = False):
        if outer:
            observer.outer_middleware(self)
        else:
            observer.middleware(self)

    def register(self, router: Router, outer: bool = False):
        for event_type in self._handlers:
            handler_name = self.pascal_case_to_snake_case(
                getattr(event_type, "__name__")
            )

            proxy = getattr(router, handler_name)

            self.install_middleware(proxy, outer)

    async def __call__(
        self,
        call_next: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        telegram_event: TelegramObject,
        data: dict[str, Any],
    ):
        for event_type, event_handler in self._handlers.items():
            if isinstance(telegram_event, event_type) or issubclass(
                event_type, type(telegram_event)
            ):
                require_data, handler = event_handler

                if require_data:
                    await handler(self, telegram_event, data)
                else:
                    await handler(self, telegram_event)

                break

        return await call_next(telegram_event, data)
