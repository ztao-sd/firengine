import asyncio
from collections.abc import AsyncGenerator

from firengine.features.stream.base_stream import BaseExchangeStream
from firengine.lib.fire_enum import SupportedExchange
from firengine.model.data_model import OrderBook


class OrderBookStream(BaseExchangeStream[OrderBook]):

    async def _generate(self) -> AsyncGenerator[OrderBook, None, None]:
        while True:
            result = await self._exchange.watch_order_book_for_symbols(list(self._symbols))
            order_book = OrderBook.from_kwargs(**result)
            yield order_book


async def demo_order_book_stream():
    ob_stream = OrderBookStream.from_supported_exchange(SupportedExchange.cryptocom)
    ob_stream.add_symbol("BTC/USD")
    ob_stream.add_symbol("ETH/USD")
    ob_stream.add_symbol("SOL/USD")
    task = asyncio.create_task(ob_stream.run())
    await asyncio.sleep(500)
    await asyncio.wait_for(task, None)
    ob_stream.stop()
    await ob_stream.close()


async def main():
    await demo_order_book_stream()


if __name__ == '__main__':
    import sys

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
