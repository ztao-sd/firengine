import asyncio
from collections.abc import Awaitable, Callable


class Signal[T]:
    def __init__(self):
        self._handlers: list[Callable[[T], None]] = []

    def emit(self, value: T):
        for handler in self._handlers:
            handler(value)

    def connect(self, func: Callable[[T], None]):
        self._handlers.append(func)

    def disconnect_all(self):
        self._handlers.clear()


class AsyncSignal[T]:
    def __init__(self):
        self._handlers: list[Callable[[T], Awaitable]] = []

    async def emit(self, value: T):
        async with asyncio.TaskGroup() as tg:
            for handler in self._handlers:
                tg.create_task(handler(value))

    def connect(self, func: Callable[[T], Awaitable]):
        self._handlers.append(func)

    def disconnect_all(self):
        self._handlers.clear()
