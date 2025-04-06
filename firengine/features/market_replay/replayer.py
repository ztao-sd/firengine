import asyncio
import traceback
from collections import defaultdict
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta

from firengine.features.market_replay.dataset_utils import (
    merge_ohlcvt_trades_for_symbols,
)
from firengine.lib.enumeration import SupportedExchange
from firengine.model.data_model import OHLCVT, TradeAbridged
from firengine.utils.timeutil import dt_to_time_ms

# async def download_data(self):
#     ohlcv_calls = math.ceil((time_ms() - self._since) / 60_000 / 300)
#     trade_calls = math.ceil((time_ms() - self._since) / 1_000 / 150)
#
#     async with asyncio.TaskGroup() as tg:
#         task1 = tg.create_task(
#             self._exchange.fetch_ohlcv(
#                 self._symbol,
#                 timeframe="1m",
#                 since=self._since,
#                 params={"paginate": True, "paginationCalls": ohlcv_calls, "maxEntriesPerRequest": 300},
#             )
#         )
#         task2 = tg.create_task(
#             self._exchange.fetch_trades(
#                 self._symbol,
#                 since=self._since,
#                 params={"paginate": True, "paginationCalls": trade_calls, "maxEntriesPerRequest": 150},
#             )
#         )
#
#     print(datetime.fromtimestamp(OHLCV(*self._ohlcvs[0]).timestamp / 1000), len(self._ohlcvs))


MarketData = OHLCVT | TradeAbridged


class TimeSeriesMarketData:
    VALID_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume", "trades", "price", "amount")

    def __init__(self, *symbols: str, timeframe: str, start_ms: int, end_ms: int):
        self._symbols = set(symbols)
        self._df = merge_ohlcvt_trades_for_symbols(self._symbols, timeframe, start_ms, end_ms)

    @property
    def symbols(self) -> set[str]:
        return self._symbols

    async def generate_ohlcvt_trade(self) -> AsyncGenerator[MarketData]:
        for v in self._df.iter_rows():
            if v[1] is not None:
                yield OHLCVT(*v[:8])
            else:
                yield TradeAbridged(v[0], v[8], v[9], v[7])


@dataclass
class ReplaySyncInfo:
    initiated = asyncio.Condition()
    completed = asyncio.Condition()
    data_points = []
    subscriber_count = 0


class MarketReplayer:
    def __init__(self, ts_data: TimeSeriesMarketData):
        self._replaying = True
        self._ts_data = ts_data
        self._sync_infos = defaultdict(lambda: defaultdict(lambda: ReplaySyncInfo()))

    def stop(self):
        self._replaying = False

    async def run(self):
        gen = self._ts_data.generate_ohlcvt_trade()
        while self._replaying:
            try:
                v = await anext(gen)
                if symbol := getattr(v, "symbol", None) and isinstance(v, MarketData):
                    sync_info = self._sync_infos[symbol][type[v]]
                    sync_info.data_points.append(v)
                    if sync_info.subscriber_count > 0:
                        async with sync_info.initiated:
                            sync_info.initiated.notify_all()

                        async with sync_info.completed:
                            await sync_info.completed.wait_for(lambda s_=sync_info: s_.subscriber_count == 0)

                        sync_info.data_points.clear()

            except Exception as err:
                traceback.print_exc()
                raise err

    @asynccontextmanager
    async def watch_data_point(self, symbol: str, dtype: type[MarketData]) -> AsyncGenerator[list[MarketData]]:
        sync_info = self._sync_infos[symbol][dtype]
        sync_info.subscriber_count += 1
        async with sync_info.initiated:
            await sync_info.initiated.wait()
        try:
            yield [p for p in sync_info.data_points]
        finally:
            sync_info.subscriber_count -= 1
            sync_info.completed.notify()


async def main():
    now = datetime.now()
    since = now - timedelta(hours=5)
    since = dt_to_time_ms(since)
    replayer = MarketReplayer.from_supported_exchange(SupportedExchange.CRYPTOCOM, "BTC/USD", since)
    await replayer.download_data()
    await replayer.close()


if __name__ == "__main__":
    import sys

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
