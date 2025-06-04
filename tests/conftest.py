import asyncio
from collections.abc import AsyncGenerator

import ccxt.pro as ccxt
import pytest
import pytest_asyncio
import uvloop

from firengine.features.exchange.exchange_instantiation import exchange_pro_instance
from firengine.features.stream.base_stream import BaseExchangeStream
from firengine.features.stream.order_stream import OrderStream
from firengine.features.stream.private_trade_stream import PrivateTradeStream
from firengine.features.trade.order_manager import OrderManager
from firengine.features.trade.otoco import OTOCOManager
from firengine.lib.enumeration import SupportedExchange


@pytest.fixture(scope="session")
def event_loop_policy():
    return uvloop.EventLoopPolicy()


exchange_params = [
    (SupportedExchange.bybit, True),
    # (SupportedExchange.kraken, False),
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


@pytest_asyncio.fixture(loop_scope="module", scope="module")
async def otoco_manager_fxt(order_manager_fxt, order_stream_fxt) -> AsyncGenerator[OTOCOManager]:
    manager = OTOCOManager(order_manager_fxt)
    order_stream_fxt.acquired.connect(manager.on_order_updated)
    yield manager
