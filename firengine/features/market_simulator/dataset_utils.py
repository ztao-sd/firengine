import os.path
from datetime import datetime, timedelta

import polars as pl

from firengine.config import KRAKEN_OHLCVT_DATA_DIR, KRAKEN_TRADES_DATA_DIR
from firengine.lib.common_type import StrPath
from firengine.utils.timeutil import parse_timeframe_to_ms

OHLCVT_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume", "trades")
TRADES_COLUMNS = ("timestamp", "price", "amount")


def get_ohlcvt_csvfile(symbol: str, timeframe: str) -> StrPath:
    ms = parse_timeframe_to_ms(timeframe)
    file = KRAKEN_OHLCVT_DATA_DIR / f"{symbol}_{ms // 60_000}.csv"
    if not os.path.exists(file):
        raise FileNotFoundError
    return file


def get_trade_csvfile(symbol: str) -> StrPath:
    file = KRAKEN_TRADES_DATA_DIR / f"{symbol}.csv"
    if not os.path.exists(file):
        raise FileNotFoundError
    return file


def read_ohlcvt_from_csv(csvfile: StrPath) -> pl.DataFrame:
    return pl.read_csv(csvfile, has_header=False, new_columns=OHLCVT_COLUMNS)


def read_trades_from_csv(csvfile: StrPath) -> pl.DataFrame:
    return pl.read_csv(csvfile, has_header=False, new_columns=TRADES_COLUMNS)


def merge_ohlcvt_trades(
    ohlcvt_csvfile: StrPath, trades_csvfile: StrPath, start_ms: int | None = None, end_ms: int | None = None
) -> pl.DataFrame:
    start_ms = start_ms // 1000 or float("-inf")
    end_ms = end_ms // 1000 or float("inf")
    ohlcvts = pl.scan_csv(ohlcvt_csvfile, has_header=False, new_columns=OHLCVT_COLUMNS).filter(
        pl.col("timestamp").is_between(start_ms, end_ms)
    )
    trades = pl.scan_csv(trades_csvfile, has_header=False, new_columns=TRADES_COLUMNS).filter(
        pl.col("timestamp").is_between(start_ms, end_ms)
    )
    return ohlcvts.join(trades, on="timestamp", how="full", coalesce=True).sort("timestamp").collect()


def merge_ohlcvt_trades_for_symbols(
    symbols: set[str],
    timeframe: str,
    start_ms: int | None = None,
    end_ms: int | None = None,
    exclude_trade: bool = False,
) -> pl.DataFrame:
    ohlcvt_csvfiles = {symbol: get_ohlcvt_csvfile(symbol, timeframe) for symbol in symbols}
    trades_csvfiles = {symbol: get_trade_csvfile(symbol) for symbol in symbols}

    start_ms = start_ms or float("-inf")
    end_ms = end_ms or float("inf")
    ohlcvts = [
        pl.scan_csv(file, has_header=False, new_columns=OHLCVT_COLUMNS)
        .with_columns((pl.col("timestamp") * 1000).cast(pl.Int64), symbol=pl.lit(symbol))
        .filter(pl.col("timestamp").is_between(start_ms, end_ms))
        for symbol, file in ohlcvt_csvfiles.items()
    ]
    ohlcvt = pl.concat(ohlcvts, how="vertical")

    if exclude_trade:
        return ohlcvt.sort("timestamp").with_columns(price=pl.lit(None), amount=pl.lit(None)).collect()
    else:
        trades = [
            pl.scan_csv(file, has_header=False, new_columns=TRADES_COLUMNS)
            .with_columns((pl.col("timestamp") * 1000).cast(pl.Int64), symbol=pl.lit(symbol))
            .filter(pl.col("timestamp").is_between(start_ms, end_ms))
            for symbol, file in trades_csvfiles.items()
        ]
        trade = pl.concat(trades, how="vertical")
        return ohlcvt.join(trade, on=["timestamp", "symbol"], how="full", coalesce=True).sort("timestamp").collect()


if __name__ == "__main__":
    f1 = KRAKEN_OHLCVT_DATA_DIR / "XBTUSD_1.csv"
    f2 = KRAKEN_TRADES_DATA_DIR / "XBTUSD.csv"
    start = (datetime.now() - timedelta(days=190)).timestamp() * 1000
    end = datetime.now().timestamp() * 1000

    symbols = {"XBTUSD", "ETHUSD"}

    merged = merge_ohlcvt_trades_for_symbols(symbols, "1m", int(start), int(end))
    print(merged)
