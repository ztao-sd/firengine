import asyncio
from collections.abc import AsyncGenerator

from ccxt.pro import Exchange

from firengine.features.data_stream.base_stream import AbstractBaseStream
from firengine.model.trading import Trade


class TradeStream(AbstractBaseStream[Trade]):
    def __init__(self, exchange: Exchange):
        super().__init__(exchange)

    async def _generate(self) -> AsyncGenerator[Trade, None, None]:
        while True:
            trade_dicts = await self._exchange.watch_trades_for_symbols(list(self._symbols))
            for d in trade_dicts:
                trade = Trade.from_kwargs(**d)
                yield trade


async def main():
    from firengine.features.data_handler import PrintDataHandler
    from firengine.lib.enumeration import SupportedExchange

    handler = PrintDataHandler[Trade]()
    stream = TradeStream.from_supported_exchange(SupportedExchange.CRYPTOCOM)
    stream.acquired.connect(handler.handle)
    stream.add_symbol("BTC/USD")
    stream.add_symbol("ETH/USD")
    task = asyncio.create_task(stream.run())
    await asyncio.sleep(20)
    stream.stop()
    await asyncio.wait_for(task, timeout=None)
    await stream.close()


if __name__ == "__main__":
    import sys

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
