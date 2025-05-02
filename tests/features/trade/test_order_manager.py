import asyncio
from collections.abc import AsyncGenerator

import ccxt.pro as ccxt
import pytest
import pytest_asyncio

from firengine.features.exchange.exchange_instantiation import exchange_pro_instance
from firengine.features.stream.base_stream import BaseExchangeStream
from firengine.features.stream.order_stream import OrderStream
from firengine.features.stream.private_trade_stream import PrivateTradeStream
from firengine.features.trade.order_manager import OrderManager
from firengine.lib.enumeration import SupportedExchange
from firengine.model.data_model import Ticker


async def fetch_ticker(ex: ccxt.Exchange, symbol: str) -> Ticker:
    d = await ex.fetch_ticker(symbol)
    return Ticker.from_kwargs(**d)


exchange_params = [
    (SupportedExchange.bybit, True),
    (SupportedExchange.kraken, False),
]


@pytest_asyncio.fixture(loop_scope="module", scope="module", params=exchange_params)
async def exchange_fxt(request) -> AsyncGenerator[ccxt.Exchange]:
    ex_name, demo = request.param
    ex = exchange_pro_instance(ex_name, f"{ex_name.name}-demo")
    if enable_demo := getattr(ex, "enable_demo_trading", None):
        enable_demo(demo)
    await ex.load_markets()
    yield ex
    await ex.close()


async def setup_stream[T: BaseExchangeStream](stream: T) -> AsyncGenerator[T]:
    task = asyncio.create_task(stream.run())
    yield stream
    stream.stop()
    await asyncio.wait_for(task, timeout=None)


@pytest_asyncio.fixture(loop_scope="module", scope="module")
async def order_stream_fxt(exchange_fxt) -> AsyncGenerator[OrderStream]:
    stream = OrderStream(exchange_fxt)
    task = asyncio.create_task(stream.run())
    yield stream
    stream.stop()
    await asyncio.wait_for(task, timeout=None)


@pytest_asyncio.fixture(loop_scope="module", scope="module")
async def trade_stream_fxt(exchange_fxt) -> AsyncGenerator[PrivateTradeStream]:
    async for stream in setup_stream(PrivateTradeStream(exchange_fxt)):
        yield stream


@pytest_asyncio.fixture(loop_scope="module", scope="module")
async def order_manager_fxt(exchange_fxt, order_stream_fxt, trade_stream_fxt) -> AsyncGenerator[OrderManager]:
    manager = OrderManager(exchange_fxt)
    order_stream_fxt.acquired.connect(manager.on_order_updated)
    trade_stream_fxt.acquired.connect(manager.on_trade_updated)
    yield manager


cancel_order_params = [("BTC/USDT:USDT", 0.001)]


@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.parametrize("symbol, amount", cancel_order_params)
async def test_create_cancel_order(exchange_fxt, order_manager_fxt, symbol: str, amount: float):
    if symbol not in exchange_fxt.symbols:
        pytest.skip(f"Symbol {symbol} not supported in {exchange_fxt.name}")

    ticker = await fetch_ticker(exchange_fxt, symbol)
    order = await order_manager_fxt.submit_order(symbol, "limit", "buy", amount, ticker.low * 0.6)
    await order_manager_fxt.cancel_order(order.id, symbol)


# @pytest.mark.asyncio(loop_scope="module")
# async def test_modify_order(order_manager_fxt):
#     order_manager, symbol, amount, price = order_manager_fxt
#     order = await order_manager.submit_order(symbol, "limit", "buy", amount, price)
#     try:
#         order.price = 20_000
#         await order_manager.modify_order(order)
#         await order_manager.refresh(symbol)
#         assert order.price == order_manager.orders[order.id].price
#     finally:
#         await order_manager.cancel_order(order.id, symbol)
