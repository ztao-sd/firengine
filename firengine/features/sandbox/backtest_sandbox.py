import asyncio
import random
from collections import deque, defaultdict
from collections.abc import AsyncGenerator

import polars as pl
import shortuuid

from firengine.config import KRAKEN_OHLCVT_DATA_DIR, SECONDS_PER_YEAR
from firengine.features.async_stream.base_stream import BaseStream
from firengine.lib.common_type import StrPath
from firengine.model.data_model import OHLCV, Order, Trade
from firengine.utils.timeutil import time_ms

OHLCVT_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume", "trades")


def load_dataframe_from_ohlcvt_csvfiles(
    csvfiles_per_symbol: dict[str, StrPath], start_ms: int | None = None, end_ms: int | None = None
):
    start_ms = start_ms or float("-inf")
    end_ms = end_ms or float("inf")
    ohlcvts = [
        pl.scan_csv(file, has_header=False, new_columns=OHLCVT_COLUMNS)
        .with_columns((pl.col("timestamp") * 1000).cast(pl.Int64), symbol=pl.lit(symbol))
        .filter(pl.col("timestamp").is_between(start_ms, end_ms))
        for symbol, file in csvfiles_per_symbol.items()
    ]
    ohlcvt = pl.concat(ohlcvts, how="vertical")
    return ohlcvt.sort("timestamp").collect()


async def generate_ohlcvt_from_df(ohlcvt_df: pl.DataFrame, speedup: int = 1) -> AsyncGenerator[OHLCV]:
    prev_time: int | None = None
    for f in ohlcvt_df.iter_rows():
        ohlcv = OHLCV(*f)
        if prev_time is None:
            prev_time = ohlcv.timestamp
        else:
            await asyncio.sleep((ohlcv.timestamp - prev_time) / 1000 / speedup)
            prev_time = ohlcv.timestamp
        yield ohlcv


async def handle_order(order: Order, orders: defaultdict[str, dict[str, Order]]):
    pass

async def main():
    # State
    ohlcv_queue: deque[OHLCV] = deque(maxlen=1_000)
    orders: dict[str, Order] = {}
    order_index = None

    # Backtest data
    speedup = 60
    symbols = ("XBTUSD",)
    files = {symbol: KRAKEN_OHLCVT_DATA_DIR / f"{symbol}_1.csv" for symbol in symbols}
    end = time_ms()
    start = end - 2 * SECONDS_PER_YEAR * 1000
    df = load_dataframe_from_ohlcvt_csvfiles(files, start, end)
    ohlcv_gen = generate_ohlcvt_from_df(df, speedup)

    # Streams
    ohlcv_stream = BaseStream[OHLCV](ohlcv_gen)
    order_stream = BaseStream[Order]()
    trade_stream = BaseStream[Trade]()

    async def print_data(data):
        print("Consumed: ", data)

    # Agent actions




    async def save_ohlcv(ohlcv: OHLCV):
        ohlcv_queue.append(ohlcv)

    async def random_strategy(ohlcv: OHLCV):
        buy_sell = random.randint(0, 1)
        if buy_sell:
            await submit_order(
                ohlcv.symbol,
                "market",
                "buy",
                0.01,
                ohlcv.low,
            )
        else:
            pass

    await ohlcv_stream.subscribe_async(print_data)
    await ohlcv_stream.subscribe_async(save_ohlcv)
    await ohlcv_stream.subscribe_async(random_strategy)

    await order_stream.subscribe_async(print_data)
    await trade_stream.subscribe_async(print_data)

    await ohlcv_stream.async_run()


if __name__ == "__main__":
    loop_factory = None

    asyncio.run(main(), loop_factory=loop_factory)
