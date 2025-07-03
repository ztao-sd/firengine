import asyncio
import logging
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import nats
import polars as pl
import shortuuid
from aioreactive.testing import VirtualTimeEventLoop
from pythonjsonlogger.orjson import OrjsonFormatter

from firengine.config import KRAKEN_OHLCVT_DATA_DIR, LOG_DIR, SECONDS_PER_YEAR
from firengine.features.async_stream.base_stream import BaseStream
from firengine.features.sandbox.backtest.backtest_trader import BacktestEngine
from firengine.lib.common_type import StrPath
from firengine.model.data_model import OHLCV, Order, Trade
from firengine.utils.timeutil import time_ms

OHLCVT_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume", "trades")


class NATSLogEventHandler(logging.Handler):
    def __init__(self, url: str):
        super().__init__()
        self._url = url
        self._nc = nats.NATS()
        self._loop = asyncio.get_running_loop()
        self._loop.run_until_complete(self._nc.connect(self._url))

    def emit(self, record: logging.LogRecord):
        try:
            if isinstance(record.msg, dict):
                strategy_name = record.msg.get("strategy_name")
                run_id = record.msg.get("run_id")
                if strategy_name and run_id:
                    subject = f"fire.{strategy_name}.{run_id}"
                    message = self.format(record)
                    self._loop.create_task(self._nc.publish(subject, message.encode()))
        except Exception as err:
            print(err)
            self.handleError(record)


def setup_standard_structured_logging(
    level: int, filename: StrPath | None = None, nats_url: str | None = None, verbose: bool = False
):
    logger = logging.getLogger()
    logger.setLevel(level)

    formatter = OrjsonFormatter("%(timestamp) %(levelname)s %(message)s", timestamp=True)

    # Stream handler
    if verbose:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        handler.setLevel(level)
        logger.addHandler(handler)

    # File handler
    if filename is not None:
        handler = logging.FileHandler(filename)
        handler.setFormatter(formatter)
        handler.setLevel(level)
        logger.addHandler(handler)

    # Nats handler
    if nats_url:
        handler = NATSLogEventHandler(nats_url)
        handler.setFormatter(formatter)
        handler.setLevel(level)
        logger.addHandler(handler)


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


async def generate_ohlcvt_from_df(
    ohlcvt_df: pl.DataFrame, speedup: int = 1, limit: int = float("inf")
) -> AsyncGenerator[OHLCV]:
    prev_time: int | None = None
    count = 0
    for f in ohlcvt_df.iter_rows():
        if count > limit:
            break
        count += 1
        ohlcv = OHLCV(*f)
        if prev_time is None:
            prev_time = ohlcv.timestamp
        else:
            await asyncio.sleep((ohlcv.timestamp - prev_time) / 1000 / speedup)
            prev_time = ohlcv.timestamp
        yield ohlcv


async def main():
    # Config data
    log_level = logging.INFO
    log_verbose = True
    strategy_name = "backtest"
    start_dt = datetime.now(UTC)
    logfile = LOG_DIR / f"{strategy_name}_{start_dt.isoformat()}_{shortuuid.uuid()}.log"
    setup_standard_structured_logging(log_level, logfile, verbose=log_verbose)

    # Backtest data
    speedup = 60
    symbols = ("XBTUSD",)
    files = {symbol: KRAKEN_OHLCVT_DATA_DIR / f"{symbol}_1.csv" for symbol in symbols}
    end = time_ms()
    start = end - 2 * SECONDS_PER_YEAR * 1000
    df = load_dataframe_from_ohlcvt_csvfiles(files, start, end)
    ohlcv_gen = generate_ohlcvt_from_df(df, speedup, limit=1000)

    # Streams
    ohlcv_stream = BaseStream[OHLCV](ohlcv_gen)
    order_stream = BaseStream[Order]()
    trade_stream = BaseStream[Trade]()

    # Engine
    trader = BacktestEngine(order_stream)

    async def print_data(data):
        pass

    await ohlcv_stream.subscribe_async(print_data)
    await ohlcv_stream.subscribe_async(trader.handle_ohlcv)
    await ohlcv_stream.subscribe_async(trader.match_open_order)

    await order_stream.subscribe_async(print_data)
    await order_stream.subscribe_async(trader.handle_order)

    await trade_stream.subscribe_async(print_data)
    await trade_stream.subscribe_async(trader.handle_trade)

    await ohlcv_stream.async_run()


if __name__ == "__main__":
    loop_factory = VirtualTimeEventLoop

    asyncio.run(main(), loop_factory=loop_factory)
