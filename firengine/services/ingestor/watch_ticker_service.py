import asyncio
import sys

import ccxt.pro as ccxt

from firengine.lib.fire_enum import SupportedExchange
from firengine.lib.model.common import CommonModel

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class WatchTickerServiceArgs(CommonModel):
    exchange: SupportedExchange
    symbol: str


async def watch_ticker_service(exchange: ):
    pass


def main():
    pass


if __name__ == "__main__":
    main()
