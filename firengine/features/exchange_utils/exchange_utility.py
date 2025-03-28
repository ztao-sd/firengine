from typing import Self

import ccxt.pro as ccxt
from ccxt.pro import Exchange

from firengine.lib.enumeration import SupportedExchange


class ExchangeUtility:
    def __init__(self, exchange: Exchange):
        self._exchange = exchange

    @classmethod
    def from_supported_exchange(cls, supp_ex: SupportedExchange) -> Self | None:
        f = getattr(ccxt, supp_ex.value, None)
        if callable(f):
            return cls(f())
        return None

    @staticmethod
    def get_supported_exchanges() -> list[SupportedExchange]:
        return [
            SupportedExchange(ex) for ex in ccxt.exchanges if ex in SupportedExchange
        ]


if __name__ == "__main__":
    exchanges = ExchangeUtility.get_supported_exchanges()
    print(exchanges)
    exchange_util = ExchangeUtility.from_supported_exchange(SupportedExchange.KRAKEN)
    print(exchange_util)
