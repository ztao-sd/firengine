import traceback
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Self

import ccxt.pro as ccxt
from ccxt.pro import Exchange

from firengine.lib.com.signal import Signal
from firengine.lib.enumeration import SupportedExchange


class AbstractBaseStream[T](ABC):
    """Data Producer"""

    def __init__(self, *args, **kwargs):
        self._symbols: set[str] = set()
        self._data_acquired_signal = Signal[T]()
        self._data_acquired_per_symbol_signal: dict[str, Signal[T]] = {}
        self._streaming = False
        self._args = args
        self._kwargs = kwargs

    @property
    def acquired(self) -> Signal[T]:
        return self._data_acquired_signal

    def acquired_per_symbol(self, symbol: str) -> Signal[T]:
        return self._data_acquired_per_symbol_signal[symbol]

    def add_symbol(self, symbol: str):
        self._symbols.add(symbol)
        self._data_acquired_per_symbol_signal[symbol] = Signal[T]()

    def remove_symbol(self, symbol: str):
        self._symbols.discard(symbol)
        self._data_acquired_per_symbol_signal.pop(symbol, None)

    @abstractmethod
    async def _generate(self) -> AsyncGenerator[T]:
        raise NotImplementedError

    async def run(self):
        self._streaming = True
        gen = self._generate()
        while self._streaming:
            try:
                data = await anext(gen)
                self._data_acquired_signal.emit(data)
                if symbol := getattr(data, "symbol", None):
                    if signal := self._data_acquired_per_symbol_signal.get(symbol):
                        signal.emit(data)
            except Exception as err:
                traceback.print_exc()
                raise err

    def stop(self):
        self._streaming = False


class BaseExchangeStream[T](AbstractBaseStream[T]):
    def __init__(self, exchange: Exchange, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._exchange = exchange

    @classmethod
    def from_supported_exchange(cls, supp_ex: SupportedExchange, *args, **kwargs) -> Self | None:
        f = getattr(ccxt, supp_ex.value, None)
        if callable(f):
            return cls(f({"newUpdates": True}), *args, **kwargs)
        return None

    async def _generate(self) -> AsyncGenerator[T, None, None]:
        raise NotImplementedError

    async def close(self):
        await self._exchange.close()
