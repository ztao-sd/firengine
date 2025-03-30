import atexit
from pprint import pprint
from typing import Self

import ccxt
from ccxt import Exchange

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

    def load_market(self):
        self._exchange.load_markets()

    @staticmethod
    def get_supported_exchanges() -> list[SupportedExchange]:
        return [SupportedExchange(ex) for ex in ccxt.exchanges if ex in SupportedExchange]

    def get_supported_methods(self) -> list[str]:
        return [k for k, v in self._exchange.has.items() if v]

    def get_timeframes(self) -> list[str]:
        return list(self._exchange.timeframes.keys())

    def get_currencies(self) -> list[str]:
        self.load_market()
        return list(self._exchange.currencies.keys())

    def get_symbols(self) -> list[str]:
        self.load_market()
        return self._exchange.symbols

    def get_pair(self, symbol: str) -> dict | None:
        self.load_market()
        return self._exchange.markets.get(symbol)

    def fetch_trades(self, symbol: str):
        return self._exchange.fetch_trades(symbol, limit=30)

    def fetch_ohlcv(self, symbol: str):
        return self._exchange.fetch_ohlcv(symbol, limit=30)


if __name__ == "__main__":
    exchanges = ExchangeUtility.get_supported_exchanges()
    # print(exchanges)
    exchange_util = ExchangeUtility.from_supported_exchange(SupportedExchange.CRYPTOCOM)
    # print(exchange_util)
    methods = exchange_util.get_supported_methods()
    pprint(methods)
    # timeframes = exchange_util.get_timeframes()
    # pprint(timeframes)
    # symbols = exchange_util.get_symbols()
    # pprint(symbols)
    # currencies = exchange_util.get_currencies()
    # pprint(currencies)
    # market = exchange_util.get_pair("BTC/USD")
    # pprint(market)
    # trades = exchange_util.fetch_trades("BTC/USD")
    # # pprint(trades)
    # olhcvs = exchange_util.fetch_ohlcv("BTC/USD")
    # pprint(olhcvs)
