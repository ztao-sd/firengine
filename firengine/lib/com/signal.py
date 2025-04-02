from collections.abc import Callable


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
