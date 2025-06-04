import asyncio

import ccxt.pro as ccxt

from firengine.features.stream.base_stream import BaseExchangeStream
from firengine.model.data_model import Ticker

tickers: dict[(str, str), Ticker] = {}


async def fetch_ticker(ex: ccxt.Exchange, symbol: str) -> Ticker:
    ticker = tickers.get((ex.name, symbol)) or Ticker.from_kwargs(**await ex.fetch_ticker(symbol))
    tickers[(ex.name, symbol)] = ticker
    return ticker


async def add_symbol_to_stream(stream: BaseExchangeStream, symbol: str):
    if symbol not in stream.symbols:
        stream.add_symbol(symbol)
        await asyncio.sleep(2.5)