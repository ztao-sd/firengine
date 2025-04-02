import asyncio
import sys
from enum import StrEnum

import ccxt.pro as ccxt

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class Symbol(StrEnum):
    BTC_USD = "BTC/USDT"


async def watch_ticker(symbol: str, timeframe: str, ticks: int):
    exchange = ccxt.kraken()

    for _ in range(ticks):
        kline = await exchange.watch_ohlcv(symbol, timeframe, limit=1)
        print("New Kline:", kline[-1])

    await exchange.close()


if __name__ == "__main__":
    asyncio.run(watch_ticker("BTC/USD", "1m", 10))
