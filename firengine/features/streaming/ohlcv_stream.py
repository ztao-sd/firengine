import asyncio
from collections import deque
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from ccxt.pro import Exchange

from firengine.features.streaming.base_stream import BaseExchangeStream
from firengine.model.data_model import OHLCV, Trade
from firengine.utils.timeutil import parse_timeframe_to_ms, time_ms

if TYPE_CHECKING:
    from firengine.features.streaming.trade_stream import TradeStream


class TradeSlidingFrame:
    def __init__(self, interval_ms: int):
        self._queue: deque[Trade] = deque()
        self._max_queue: deque[Trade] = deque()
        self._min_queue: deque[Trade] = deque()
        self._volume_sum: float = 0.0
        self._interval_ms = interval_ms
        # self._opening: int | None = None
        self._last_opening: int | None = None

    def put(self, trade: Trade):
        # Refresh opening time
        # if self._opening is None or trade.timestamp > self._opening + self._interval_ms:
        #     self._opening = trade.timestamp
        # Append to queue
        self._queue.appendleft(trade)
        self._volume_sum += trade.amount

        while self._max_queue and self._max_queue[0].price <= trade.price:
            self._max_queue.popleft()
        self._max_queue.appendleft(trade)

        while self._min_queue and self._min_queue[0].price >= trade.price:
            self._min_queue.popleft()
        self._min_queue.appendleft(trade)

        # Evict
        # self.evict(self._opening)

    def evict(self, opening: int):
        while self._queue and self._queue[-1].timestamp < opening:
            evicted = self._queue.pop()
            self._volume_sum -= evicted.amount
            if evicted is self._max_queue[-1]:
                self._max_queue.pop()
            if evicted is self._min_queue[-1]:
                self._min_queue.pop()

    def get_ohlcv(self) -> OHLCV | None:
        if self._queue:
            # assert self._max_queue[-1].price == max(t.price for t in self._queue)
            # assert self._min_queue[-1].price == min(t.price for t in self._queue)
            return OHLCV(
                timestamp=self._queue[-1].timestamp,
                open=self._queue[-1].price,
                high=self._max_queue[-1].price,
                low=self._min_queue[-1].price,
                close=self._queue[0].price,
                volume=self._volume_sum,
            )
        return None

    def get_next_ohlcv(self) -> OHLCV | None:
        now = time_ms()
        self._last_opening = self._last_opening or now
        closing = self._last_opening + self._interval_ms
        # print(close - now)
        if now > closing:
            self.evict(self._last_opening)
            # print(self._last_opening, self._queue[-1].timestamp if self._queue else None)
            self._last_opening = closing
            return self.get_ohlcv()
        return None


class LocalOHLCVStream(BaseExchangeStream[OHLCV]):
    def __init__(
        self,
        exchange: Exchange,
        timeframe: str,
        trade_stream: "TradeStream",
    ):
        super().__init__(exchange)
        self._timeframe = timeframe
        self._trade_stream = trade_stream
        self._interval_ms = parse_timeframe_to_ms(timeframe)

        self._sliding_frames: dict[str, TradeSlidingFrame] = {}
        self._trade_stream.acquired.connect(self.put_trade_to_frame)
        self._sleep_time = min(1000, self._interval_ms // 30) / 1000  # in sec

    def add_symbol(self, symbol):
        super().add_symbol(symbol)
        self._sliding_frames[symbol] = TradeSlidingFrame(self._interval_ms)

    def remove_symbol(self, symbol):
        super().remove_symbol(symbol)
        self._sliding_frames.pop(symbol, None)

    def put_trade_to_frame(self, trade: Trade):
        if frame := self._sliding_frames.get(trade.symbol):
            frame.put(trade)

    async def _generate(self) -> AsyncGenerator[OHLCV, None, None]:
        while True:
            for symbol, frame in self._sliding_frames.items():
                if ohlcv := frame.get_next_ohlcv():
                    ohlcv.timeframe = self._timeframe
                    ohlcv.symbol = symbol
                    print(symbol, self._exchange.iso8601(ohlcv.timestamp), ohlcv)
                    yield ohlcv
            await asyncio.sleep(self._sleep_time)


class RemoteOHLCVStream(BaseExchangeStream[OHLCV]):
    def __init__(self, exchange, timeframe: str):
        super().__init__(exchange)
        self._timeframe = timeframe
        self._tasks: dict[str, asyncio.Task] = {}

    async def _get_ohlcv(self, symbol: str, timeframe: str) -> list[OHLCV]:
        results = await self._exchange.watch_ohlcv(symbol, timeframe=timeframe)
        ohlcvs = []
        for d in results:
            ohlcv = OHLCV(*d)
            ohlcv.symbol = symbol
            ohlcv.timeframe = timeframe
            ohlcvs.append(ohlcv)
        return ohlcvs

    async def _generate(self) -> AsyncGenerator[OHLCV, None, None]:
        while True:
            results = []
            for symbol in self._symbols:
                task = self._tasks.get(symbol)
                if task is None:
                    task = asyncio.create_task(self._get_ohlcv(symbol, timeframe=self._timeframe))
                    self._tasks[symbol] = task

            await asyncio.wait(self._tasks.values(), return_when=asyncio.FIRST_COMPLETED)

            for symbol in self._symbols:
                if task := self._tasks.get(symbol):
                    if task.done():
                        results.extend(task.result())
                        self._tasks.pop(symbol, None)

            for result in results:
                print(result)
                yield result


async def demo_local_ohlcv_stream():
    from firengine.features.data_handler import PrintDataHandler
    from firengine.features.streaming.trade_stream import TradeStream
    from firengine.lib.enumeration import SupportedExchange

    trade_stream = TradeStream.from_supported_exchange(SupportedExchange.CRYPTOCOM)
    ohlcv_stream = LocalOHLCVStream.from_supported_exchange(
        SupportedExchange.CRYPTOCOM, timeframe="1m", trade_stream=trade_stream
    )
    streams = [trade_stream, ohlcv_stream]
    # handler = PrintDataHandler[Trade]()
    # trade_stream.acquired.connect(handler.handle)
    for stream in streams:
        stream.add_symbol("BTC/USD")
        stream.add_symbol("ETH/USD")
    tasks = [asyncio.create_task(trade_stream.run()), asyncio.create_task(ohlcv_stream.run())]
    await asyncio.sleep(1200)
    trade_stream.stop()
    ohlcv_stream.stop()
    for task in tasks:
        await asyncio.wait_for(task, timeout=None)
    await trade_stream.close()
    await ohlcv_stream.close()


async def demo_remote_ohlcv_stream():
    from firengine.lib.enumeration import SupportedExchange

    ohlcv_stream = RemoteOHLCVStream.from_supported_exchange(
        SupportedExchange.CRYPTOCOM,
        timeframe="1m",
    )
    streams = [ohlcv_stream]
    # handler = PrintDataHandler[Trade]()
    # trade_stream.acquired.connect(handler.handle)
    for stream in streams:
        stream.add_symbol("BTC/USD")
        stream.add_symbol("ETH/USD")
        stream.add_symbol("SOL/USD")
    tasks = [asyncio.create_task(ohlcv_stream.run())]
    await asyncio.sleep(1200)
    ohlcv_stream.stop()
    for task in tasks:
        await asyncio.wait_for(task, timeout=None)
    await ohlcv_stream.close()


async def main():
    await demo_remote_ohlcv_stream()


if __name__ == "__main__":
    import sys

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
