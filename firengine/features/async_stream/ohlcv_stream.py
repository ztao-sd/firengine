import asyncio
import time
import traceback
from collections.abc import AsyncGenerator, AsyncIterable
from typing import TYPE_CHECKING, Optional, Union

import polars as pl
from aioreactive import AsyncObserver, AsyncSubject, filter
from expression import pipe
from expression.system import AsyncDisposable

from firengine.lib.common_type import StrPath
from firengine.model.data_model import OHLCV

if TYPE_CHECKING:
    from aioreactive import CloseAsync, SendAsync, ThrowAsync

OHLCVT_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume", "trades")


def load_dataframe_from_ohlcvt_csvfiles(
    csvfiles_per_symbol: dict[str, StrPath], start_ms: int | None = None, end_ms: int | None = None
):
    ohlcvts = [
        pl.scan_csv(file, has_header=False, new_columns=OHLCVT_COLUMNS)
        .with_columns((pl.col("timestamp") * 1000).cast(pl.Int64), symbol=pl.lit(symbol))
        .filter(pl.col("timestamp").is_between(start_ms, end_ms))
        for symbol, file in csvfiles_per_symbol.items()
    ]
    ohlcvt = pl.concat(ohlcvts, how="vertical")
    return ohlcvt.sort("timestamp").with_columns(price=pl.lit(None), amount=pl.lit(None)).collect()


async def generate_ohlcvt_from_df(ohlcvt_df: pl.DataFrame) -> AsyncGenerator[OHLCV]:
    for f in ohlcvt_df.iter_rows():
        yield OHLCV(*f)


class BaseStream[T](AsyncSubject):
    def __init__(self, async_iter: AsyncIterable[T]):
        super().__init__()
        self._async_iter = async_iter
        self._streaming = False

    async def async_run(self):
        self._streaming = True
        async_iter = aiter(self._async_iter)
        while self._streaming:
            try:
                obj = await anext(async_iter)
                await self.asend(obj)
            except StopAsyncIteration as err:
                self._streaming = False
                print("stop", err)
                traceback.print_exc()
            except Exception as err:
                print(err)
                traceback.print_exc()


class BacktestOHLCVStream(BaseStream):
    def __init__(self, ohlcvs: AsyncIterable[OHLCV]):
        super().__init__(ohlcvs)

        # State
        self._streaming = False

    @classmethod
    def from_csv_files(
        cls, csvfiles_per_symbol: dict[str, StrPath], start_ms: int | None = None, end_ms: int | None = None
    ):
        df = load_dataframe_from_ohlcvt_csvfiles(csvfiles_per_symbol, start_ms, end_ms)
        ohlcvs = generate_ohlcvt_from_df(df)
        return cls(ohlcvs)

    async def subscribe_async_by_symbol(
        self,
        symbol: str,
        send: Union["SendAsync[OHLCV]", "AsyncObserver[OHLCV]", None] = None,
        throw: Optional["ThrowAsync"] = None,
        close: Optional["CloseAsync"] = None,
    ) -> "AsyncDisposable":
        def predicate(value: OHLCV):
            return value.symbol == symbol

        xs = pipe(self, filter(predicate))
        return await xs.subscribe_async(send, throw, close)


async def main():
    import random

    def generic_ohlcv() -> OHLCV:
        return OHLCV(
            random.randint(0, int(time.time())),
            random.uniform(0.0, 1000.0),
            random.uniform(0.0, 1000.0),
            random.uniform(0.0, 1000.0),
            random.uniform(0.0, 1000.0),
            random.uniform(0.0, 1000.0),
            symbol=random.choice(["BTC/UDS", "ETH/EUR"]),
        )

    async def ohlcv_iterator() -> AsyncGenerator[OHLCV]:
        for _ in range(100):
            yield generic_ohlcv()

    stream = BacktestOHLCVStream(ohlcv_iterator())

    async def received(ohlcv: OHLCV):
        print(ohlcv)

    await stream.subscribe_async_by_symbol("ETH/EUR", received)
    await stream.async_run()


if __name__ == "__main__":
    from aioreactive.testing.virtual_events import VirtualTimeEventLoop

    asyncio.run(main(), loop_factory=VirtualTimeEventLoop)
