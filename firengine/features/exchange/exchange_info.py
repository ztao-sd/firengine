from dataclasses import dataclass
from typing import Self

import ccxt

@dataclass
class ExchangeInfo:
    currencies: set[str]
    symbols: set[str]
    timeframes: set[str]
    supported_methods: set[str]


    @classmethod
    def from_exchange(cls, ex: ccxt.Exchange) -> Self:
        ex.load_markets()
        return cls(
            currencies=set(ex.currencies.keys()),
            symbols=set(ex.symbols),
            timeframes=set(ex.timeframes.keys()),
            supported_methods=set(k for k, v in ex.has.items() if v)
        )

    @classmethod
    def bybit(cls, ex: ccxt.bybit) -> Self:
        return cls.from_exchange(ex)

    @classmethod
    def kraken(cls, ex: ccxt.kraken) -> Self:
        return cls.from_exchange(ex)


if __name__ == '__main__':
    i1 = ExchangeInfo.bybit(ccxt.bybit())
    i2 = ExchangeInfo.kraken(ccxt.kraken())
    print(i1)
    print(i2)