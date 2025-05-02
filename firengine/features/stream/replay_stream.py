import asyncio
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from firengine.features.stream.base_stream import AbstractBaseStream
from firengine.model.data_model import OHLCV, Trade
from firengine.utils.timeutil import past_timestamp_ms

if TYPE_CHECKING:
    from firengine.features.market_replay.replayer import MarketReplayer


SupportDataType = OHLCV | Trade


class OHLCVReplayStream(AbstractBaseStream[OHLCV]):
    def __init__(self, replayer: "MarketReplayer"):
        super().__init__()
        self._replayer = replayer

    def add_symbol(self, symbol: str):
        if symbol not in self._symbols:
            self._replayer.add_subscriber(symbol, OHLCV)
        super().add_symbol(symbol)

    async def _generate(self) -> AsyncGenerator[OHLCV]:
        while True:
            if symbol := next(iter(self._symbols), None):
                async with self._replayer.watch_data_point(symbol, dtype=OHLCV) as points:
                    for point in points:
                        print(point)
                        yield point


async def main():
    from firengine.features.market_replay.replayer import MarketReplayer, TimeSeriesMarketData

    symbols = ["XBTUSD"]
    start = past_timestamp_ms(days=190)
    end = past_timestamp_ms()
    ts_data = TimeSeriesMarketData(*symbols, timeframe="1m", start_ms=start, end_ms=end, exclude_trade=True)
    replayer = MarketReplayer(ts_data=ts_data, speedup=60.0)
    stream = OHLCVReplayStream(replayer=replayer)
    stream.add_symbol("XBTUSD")

    asyncio.create_task(stream.run())
    task1 = asyncio.create_task(replayer.run())

    await asyncio.wait([task1])

if __name__ == '__main__':
    import sys

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())