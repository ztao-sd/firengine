import asyncio
from collections.abc import AsyncGenerator
from copy import copy

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

tickers: dict[(str, str), Ticker] = {}


async def fetch_ticker(ex: ccxt.Exchange, symbol: str) -> Ticker:
    ticker = tickers.get((ex.name, symbol)) or Ticker.from_kwargs(**await ex.fetch_ticker(symbol))
    tickers[(ex.name, symbol)] = ticker
    return ticker


async def add_symbol_to_stream(stream: BaseExchangeStream, symbol: str):
    if symbol not in stream.symbols:
        stream.add_symbol(symbol)
        await asyncio.sleep(2.5)


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


cancel_order_params = [("BTC/USDT:USDT", 0.001)]


@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.parametrize("symbol, amount", cancel_order_params)
async def test_create_cancel_order(
    exchange_fxt, order_manager_fxt, order_stream_fxt, trade_stream_fxt, symbol: str, amount: float
):
    if symbol not in exchange_fxt.symbols:
        pytest.skip(f"Symbol {symbol} not supported in {exchange_fxt.name}")

    # Add symbol
    async with asyncio.TaskGroup() as tg:
        for stream in (order_stream_fxt, trade_stream_fxt):
            tg.create_task(add_symbol_to_stream(stream, symbol))
        task = tg.create_task(fetch_ticker(exchange_fxt, symbol))
    ticker = task.result()

    order = await order_manager_fxt.submit_order(symbol, "limit", "buy", amount, ticker.low * 0.6)
    await asyncio.sleep(1.0)
    assert order.id in order_manager_fxt.get_open_orders_per_symbol(symbol)
    await order_manager_fxt.cancel_order(order.id, symbol)
    await asyncio.sleep(1.0)
    assert order.id not in order_manager_fxt.get_open_orders_per_symbol(symbol)


cancel_order_params = [("BTC/USDT:USDT", 0.001, 0.6, 0.5)]


@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.parametrize("symbol, amount, price_ratio, new_price_ratio", cancel_order_params)
async def test_modify_order(
    exchange_fxt,
    order_manager_fxt,
    order_stream_fxt,
    trade_stream_fxt,
    symbol: str,
    amount: float,
    price_ratio: float,
    new_price_ratio: float,
):
    if symbol not in exchange_fxt.symbols:
        pytest.skip(f"Symbol {symbol} not supported in {exchange_fxt.name}")

    # Add symbol
    async with asyncio.TaskGroup() as tg:
        for stream in (order_stream_fxt, trade_stream_fxt):
            tg.create_task(add_symbol_to_stream(stream, symbol))
        task = tg.create_task(fetch_ticker(exchange_fxt, symbol))
    ticker = task.result()

    order_info = await order_manager_fxt.submit_order(symbol, "limit", "buy", amount, ticker.low * price_ratio)
    await asyncio.sleep(1.0)
    try:
        order = copy(order_manager_fxt.get_open_order(symbol, order_info.id))
        order.price = ticker.low * new_price_ratio
        await order_manager_fxt.modify_order(order)
        await asyncio.sleep(1.0)
        order = order_manager_fxt.get_open_order(symbol, order_info.id)
        assert order.price == pytest.approx(ticker.low * new_price_ratio, rel=1e-3)
    finally:
        await order_manager_fxt.cancel_order(order_info.id, symbol)


fill_order_params = ["BTC/USDT:USDT"]


@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.parametrize("symbol", fill_order_params)
async def test_fill_order(exchange_fxt, order_manager_fxt, order_stream_fxt, trade_stream_fxt, symbol):
    if symbol not in exchange_fxt.symbols:
        pytest.skip(f"Symbol {symbol} not supported in {exchange_fxt.name}")

    # Add symbol
    async with asyncio.TaskGroup() as tg:
        for stream in (order_stream_fxt, trade_stream_fxt):
            tg.create_task(add_symbol_to_stream(stream, symbol))
        task = tg.create_task(fetch_ticker(exchange_fxt, symbol))
    ticker = task.result()

    amount = 0.001
    order_info = await order_manager_fxt.submit_order(symbol, "limit", "buy", amount, ticker.low * 0.6)
    await asyncio.sleep(1.0)
    try:
        order = copy(order_manager_fxt.get_open_order(symbol, order_info.id))
        order.price = ticker.high * 1.2
        await order_manager_fxt.modify_order(order)
        await asyncio.sleep(1.0)
        assert not order_manager_fxt.get_open_order(symbol, order_info.id)
        assert order_manager_fxt.get_closed_order(symbol, order_info.id)
        assert len(order_manager_fxt.get_trades_per_order(order_info.id)) == 1
    finally:
        await order_manager_fxt.cancel_all_orders(symbol)


cancel_all_orders_params = ["BTC/USDT:USDT"]


@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.parametrize("symbol", cancel_all_orders_params)
async def test_cancel_all_orders(exchange_fxt, order_manager_fxt, order_stream_fxt, trade_stream_fxt, symbol):
    if symbol not in exchange_fxt.symbols:
        pytest.skip(f"Symbol {symbol} not supported in {exchange_fxt.name}")

    # Add symbol
    async with asyncio.TaskGroup() as tg:
        for stream in (order_stream_fxt, trade_stream_fxt):
            tg.create_task(add_symbol_to_stream(stream, symbol))
        task = tg.create_task(fetch_ticker(exchange_fxt, symbol))
    ticker = task.result()

    amount = 0.001
    order_infos = []
    for _ in range(5):
        order_info = await order_manager_fxt.submit_order(symbol, "limit", "buy", amount, ticker.low * 0.6)
        order_infos.append(order_info)
    for _ in range(5):
        order_info = await order_manager_fxt.submit_order(symbol, "limit", "sell", amount, ticker.low * 1.5)
        order_infos.append(order_info)
    await asyncio.sleep(1.0)
    for order_info in order_infos:
        assert order_info.id in order_manager_fxt.get_open_orders_per_symbol(symbol)
    await order_manager_fxt.cancel_all_orders(symbol)
    await asyncio.sleep(20.0)
    assert not order_manager_fxt.get_open_orders_per_symbol(symbol)
