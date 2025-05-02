import asyncio
from collections.abc import AsyncGenerator

import ccxt.pro as ccxt

from firengine.features.stream.base_stream import BaseExchangeStream
from firengine.model.data_model import Order


class OrderStream(BaseExchangeStream[Order]):
    def __init__(self, exchange: ccxt.Exchange):
        super().__init__(exchange)
        self._tasks: dict[str, asyncio.Task] = {}


    async def _generate(self) -> AsyncGenerator[Order | None, None, None]:
        while True:
            if results := await self._multi_symbol_handler(self._symbols, self._tasks, self._exchange.watch_orders):
                for d in results:
                    order = Order.from_kwargs(**d)
                    yield order
            else:
                await asyncio.sleep(0.1)
                yield None


if __name__ == "__main__":
    pass