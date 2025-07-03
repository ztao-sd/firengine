import asyncio
import traceback
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Awaitable, Callable, Collection
from typing import Any, Self

import ccxt.pro as ccxt
from ccxt.pro import Exchange

from firengine.lib.com.signal import AsyncSignal
from firengine.lib.fire_enum import SupportedExchange


class AbstractBaseStream[T](ABC):
    """Data Producer"""

    def __init__(self, *args, **kwargs):
        self._symbols: set[str] = set()
        self._data_acquired_signal = AsyncSignal[T]()
        self._data_acquired_per_symbol_signal: dict[str, AsyncSignal[T]] = {}
        self._streaming = False
        self._args = args
        self._kwargs = kwargs

    @property
    def acquired(self) -> AsyncSignal[T]:
        return self._data_acquired_signal

    @property
    def symbols(self) -> set[str]:
        return self._symbols

    def acquired_per_symbol(self, symbol: str) -> AsyncSignal[T]:
        return self._data_acquired_per_symbol_signal[symbol]

    def add_symbol(self, symbol: str):
        self._symbols.add(symbol)
        self._data_acquired_per_symbol_signal[symbol] = AsyncSignal[T]()

    def remove_symbol(self, symbol: str):
        self._symbols.discard(symbol)
        self._data_acquired_per_symbol_signal.pop(symbol, None)

    @abstractmethod
    async def _generate(self) -> AsyncGenerator[T | None]:
        raise NotImplementedError

    async def run(self):
        self._streaming = True
        gen = self._generate()
        while self._streaming:
            try:
                if data := await anext(gen):
                    await self._data_acquired_signal.emit(data)
                    if symbol := getattr(data, "symbol", None):
                        if signal := self._data_acquired_per_symbol_signal.get(symbol):
                            await signal.emit(data)
            except Exception as err:
                traceback.print_exc()
                raise err

    def stop(self):
        self._streaming = False

    @staticmethod
    async def _multi_symbol_handler(
        symbols: Collection[str], tasks: dict[str, asyncio.Task], func: Callable[[..., Any], Awaitable], *args, **kwargs
    ) -> list[Any]:
        results = []
        for symbol in symbols:
            task = tasks.get(symbol)
            if task is None:
                task = asyncio.create_task(func(symbol, *args, **kwargs))
                tasks[symbol] = task

        if tasks:
            await asyncio.wait(tasks.values(), return_when=asyncio.FIRST_COMPLETED, timeout=5.0)

        for symbol in symbols:
            if task := tasks.get(symbol):
                if task.done():
                    results.extend(task.result())
                    tasks.pop(symbol, None)
        return results


class BaseExchangeStream[T](AbstractBaseStream[T]):
    def __init__(self, exchange: Exchange, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._exchange = exchange

    @classmethod
    def from_supported_exchange(
        cls,
        supp_ex: SupportedExchange,
        *args,
        demo: bool = False,
        **kwargs,
    ) -> Self | None:
        f = getattr(ccxt, supp_ex.value, None)
        ex = f({"newUpdates": True})
        if demo:
            ex.enable_demo_trading(True)
        if callable(f):
            return cls(ex, *args, **kwargs)
        return None

    async def _generate(self) -> AsyncGenerator[T | None]:
        raise NotImplementedError

    async def close(self):
        await self._exchange.close()
