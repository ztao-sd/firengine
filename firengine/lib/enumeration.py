from enum import StrEnum, auto


class SupportedExchange(StrEnum):
    kraken = auto()
    ndax = auto()
    cryptocom = auto()
    bybit = auto()


class Symbol(StrEnum):
    BTCUSDT = "BTC/USDT"


class OrderStatus(StrEnum):
    open = auto()
    close = auto()
    pending = auto()


class OrderType(StrEnum):
    market = auto()
    limit = auto()