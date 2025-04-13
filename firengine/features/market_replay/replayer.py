import asyncio
import traceback
from collections import defaultdict
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta

from firengine.features.market_replay.dataset_utils import (
    merge_ohlcvt_trades_for_symbols,
)
from firengine.model.data_model import OHLCV, Trade
from firengine.utils.iterator import peek

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


MarketData = OHLCV | Trade


class TimeSeriesMarketData:
    VALID_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume", "trades", "price", "amount")

    def __init__(self, *symbols: str, timeframe: str, start_ms: int, end_ms: int, exclude_trade: bool = False):
        self._symbols = set(symbols)
        self._df = merge_ohlcvt_trades_for_symbols(self._symbols, timeframe, start_ms, end_ms, exclude_trade)

    @property
    def symbols(self) -> set[str]:
        return self._symbols

    def generate_ohlcvt_trade(self) -> Generator[MarketData]:
        for v in self._df.iter_rows():
            if v[8] is not None:
                yield Trade(v[0], v[8], v[9], v[7])
            if v[1] is not None:
                yield OHLCV(*v[:8])


@dataclass
class ReplaySyncInfo:
    initiated = asyncio.Condition()
    completed = asyncio.Condition()
    data_points = []
    completed_count = 0
    subscriber_count = 0


class MarketReplayer:
    def __init__(self, ts_data: TimeSeriesMarketData, speedup: float = float("inf")):
        self._speedup = speedup
        self._replaying = True
        self._ts_data = ts_data
        self._sync_infos = defaultdict(lambda: defaultdict(lambda: ReplaySyncInfo()))

    def stop(self):
        self._replaying = False

    def add_subscriber(self, symbol: str, dtype: type[MarketData]):
        self._sync_infos[symbol][dtype].subscriber_count += 1

    async def run(self):
        loop = asyncio.get_running_loop()
        gen = self._ts_data.generate_ohlcvt_trade()
        while self._replaying:
            try:
                v = next(gen)
                start = loop.time()
                symbol = getattr(v, "symbol", None)
                if isinstance(v, MarketData) and symbol is not None:
                    sync_info = self._sync_infos[symbol][type(v)]
                    sync_info.data_points.append(v)
                    if sync_info.subscriber_count > 0:
                        async with sync_info.initiated:
                            sync_info.initiated.notify_all()

                        async with sync_info.completed:
                            await sync_info.completed.wait_for(
                                lambda s_=sync_info: s_.completed_count == s_.subscriber_count
                            )
                            sync_info.completed_count = 0

                        sync_info.data_points.clear()

                    # Compute sleep time
                    next_v = peek(gen)
                    elapsed = loop.time() - start
                    t_diff = (next_v.timestamp - v.timestamp) / 1000
                    sleep_time = (t_diff - elapsed) / self._speedup
                    if sleep_time > 0:
                        await asyncio.sleep(sleep_time)
            except StopIteration:
                break
            except Exception as err:
                traceback.print_exc()
                raise err

    @asynccontextmanager
    async def watch_data_point(self, symbol: str, dtype: type[MarketData]) -> AsyncGenerator[list[MarketData]]:
        sync_info = self._sync_infos[symbol][dtype]
        async with sync_info.initiated:
            await sync_info.initiated.wait()
        try:
            yield [p for p in sync_info.data_points]
        finally:
            sync_info.completed_count += 1
            async with sync_info.completed:
                sync_info.completed.notify()


async def main():
    symbols = ["XBTUSD", "ETHUSD"]
    start = (datetime.now() - timedelta(days=190)).timestamp() * 1000
    end = datetime.now().timestamp() * 1000
    data = TimeSeriesMarketData(*symbols, timeframe="1m", start_ms=int(start), end_ms=int(end), exclude_trade=False)
    replayer = MarketReplayer(ts_data=data)
    task = asyncio.create_task(replayer.run())
    print("dfsd")
    await asyncio.wait([task])


if __name__ == "__main__":
    import sys

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
