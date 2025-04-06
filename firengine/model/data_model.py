from dataclasses import dataclass, fields
from typing import Self


class FromDictMixin:
    @classmethod
    def from_kwargs(cls, **kwargs) -> Self:
        return cls(**{f.name: kwargs.get(f.name) for f in fields(cls)})


@dataclass
class Trade(FromDictMixin):
    id: int
    timestamp: int  # ms
    symbol: str
    side: str
    type: str
    price: float
    amount: float
    cost: float


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
    timeframe: str | None = None
    symbol: str | None = None


@dataclass
class OHLCVT:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    trades: int
    timeframe: str | None = None
    symbol: str | None = None

@dataclass
class OrderBook(FromDictMixin):
    bids: list[list[float]]
    asks: list[list[float]]
    symbol: str
    timestamp: int
    datetime: str
    nonce: int
