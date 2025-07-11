from dataclasses import dataclass, fields
from typing import Self

from firengine.lib.fire_enum import OrderStatus, OrderType, TimeInForce, TradeSide


class FromDictMixin:
    @classmethod
    def from_kwargs(cls, **kwargs) -> Self:
        return cls(**{f.name: kwargs.get(f.name) for f in fields(cls)})


@dataclass
class Ticker(FromDictMixin):
    symbol: str
    timestamp: int
    datetime: str
    high: float
    low: float
    bid: float
    bidVolume: float
    ask: float
    askVolume: float
    vmap: float
    open: float
    close: float
    last: float
    previousClose: float
    change: float
    percentage: float
    average: float
    baseVolume: float
    quoteVolume: float


@dataclass
class Trade(FromDictMixin):
    timestamp: int  # ms
    price: float
    amount: float
    symbol: str | None = None
    id: int | None = None
    side: str | None = None
    type: str | None = None
    cost: float | None = None


@dataclass
class TradeAbridged:
    timestamp: int
    price: float
    amount: float
    symbol: str | None = None


@dataclass(frozen=True)
class OHLCV:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    trades: int | None = None
    symbol: str | None = None
    timeframe: str | None = None


@dataclass
class OrderBook(FromDictMixin):
    bids: list[list[float]]
    asks: list[list[float]]
    symbol: str
    timestamp: int
    datetime: str
    nonce: int


@dataclass
class PrivateTrade(FromDictMixin):
    id: str
    timestamp: int
    datetime: str
    symbol: str
    order: str
    type: str
    side: str
    takerOrMaker: str
    price: float
    amount: float
    cost: float
    fee: dict
    fees: dict


@dataclass
class OrderRequest(FromDictMixin):
    symbol: str
    type: str
    side: str
    amount: float
    price: float


@dataclass
class Order(FromDictMixin):
    id: str
    clientOrderId: str
    datetime: str
    timestamp: int
    lastTradeTimestamp: int
    status: OrderStatus
    symbol: str
    type: OrderType
    timeInForce: TimeInForce
    side: TradeSide
    price: float
    average: float
    amount: float
    filled: float
    remaining: float
    cost: float
    trades: list
    fee: dict


@dataclass
class OrderInfo(FromDictMixin):
    id: str
    symbol: str
    type: str
    side: str
    amount: float
    price: float
    triggerPrice: float | None = None
    timeInForce: str = "GTC"
    status: OrderStatus = OrderStatus.pending


@dataclass
class OTOCO(FromDictMixin):
    id: str
    symbol: str
    side: str
    amount: float
    price: float
    tp_price: float
    sl_price: float
    order_id: str | None = None
    tp_order_id: str | None = None
    sl_order_id: str | None = None
