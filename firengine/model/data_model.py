from dataclasses import dataclass, fields
from typing import Self


class FromDictMixin:
    @classmethod
    def from_kwargs(cls, **kwargs) -> Self:
        return cls(**{f.name: kwargs.get(f.name) for f in fields(cls)})


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


@dataclass
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
class PrivateTrade:
    id: str
    timestamp: int
    datetime: str
    symbol: str
    type: str
    side: str
    takerOrMaker: str
    price: float
    amount: float
    cost: float

@dataclass
class Order:
    pass