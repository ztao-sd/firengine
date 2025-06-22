from enum import StrEnum, auto


class SupportedExchange(StrEnum):
    kraken = auto()
    ndax = auto()
    cryptocom = auto()
    bybit = auto()


class Symbol(StrEnum):
    BTCUSDT = "BTC/USDT"


class TradeSide(StrEnum):
    buy = auto()
    sell = auto()


class OrderStatus(StrEnum):
    open = auto()
    close = auto()
    canceled = auto()
    expired = auto()
    rejected = auto()
    pending = auto()


class OrderType(StrEnum):
    market = auto()
    limit = auto()


class TimeInForce(StrEnum):
    good_till_cancel = "GTC"
    immediate_or_cancel = "IOC"
    fill_or_kill = "FOK"
    post_only = "PO"

class TakerOrMaker(StrEnum):
    taker = auto()
    maker = auto()
