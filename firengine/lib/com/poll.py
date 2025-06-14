from collections.abc import Callable


class Poller[T]:
    def __init__(self, default_factory: Callable[[], T], default_value: T | None = None):
        if default_value is not None:
            self._default_value = default_value
        else:
            self._default_value = default_factory()
        self._getter = None

    @property
    def value(self) -> T:
        return self._getter() if self._getter is not None else self._default_value

    def poll(self, getter: Callable[[], T]):
        self._getter = getter
