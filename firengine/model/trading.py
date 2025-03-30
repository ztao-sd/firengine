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
class OHLCV:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    timeframe: str | None = None
