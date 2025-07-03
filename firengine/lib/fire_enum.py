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


class EventType(StrEnum):
    start_run = auto()
    end_run = auto()
    collect_ohlcv = auto()
    submit_order = auto()
    modify_order = auto()
    cancel_order = auto()
    fill_order = auto()

class Currency(StrEnum):
    pass
