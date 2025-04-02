from enum import StrEnum, auto


class SupportedExchange(StrEnum):
    KRAKEN = auto()
    NDAX = auto()
    CRYPTOCOM = auto()


class Symbol(StrEnum):
    BTCUSDT = "BTC/USDT"
