import asyncio
from collections.abc import AsyncGenerator

from ccxt.pro import Exchange

from firengine.features.stream.base_stream import BaseExchangeStream
from firengine.model.data_model import PrivateTrade


class PrivateTradeStream(BaseExchangeStream[PrivateTrade]):
    def __init__(self, exchange: Exchange):
        super().__init__(exchange)
        self._tasks: dict[str, asyncio.Task] = {}

    async def _generate(self) -> AsyncGenerator[PrivateTrade | None, None, None]:
        while True:
            if dicts_ := await self._multi_symbol_handler(self._symbols, self._tasks, self._exchange.watch_my_trades):
                for d in dicts_:
                    yield PrivateTrade.from_kwargs(**d)
            else:
                await asyncio.sleep(0.1)
                yield None


if __name__ == "__main__":
    import ccxt.pro as ccxt

    ex = ccxt.bybit()
    ex.watch_my_trades()
