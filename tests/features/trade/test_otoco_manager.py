import asyncio
from copy import copy
from datetime import datetime

import pytest

from firengine.utils.test_utils import add_symbol_to_stream, fetch_ticker

ocoto_manager_params = [("BTC/USDT:USDT", "buy", 0.001, 1.5, 0.5)]


@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.parametrize("symbol, side, amount, tp_ratio, sl_ratio", ocoto_manager_params)
async def test_otoco_manager(
    exchange_fxt,
    otoco_manager_fxt,
    order_manager_fxt,
    order_stream_fxt,
    trade_stream_fxt,
    symbol: str,
    side: str,
    amount: float,
    tp_ratio: float,
    sl_ratio: float,
):
    if symbol not in exchange_fxt.symbols:
        pytest.skip(f"Symbol {symbol} not supported in {exchange_fxt.name}")

    # Add symbol
    async with asyncio.TaskGroup() as tg:
        for stream in (order_stream_fxt, trade_stream_fxt):
            tg.create_task(add_symbol_to_stream(stream, symbol))
        task = tg.create_task(fetch_ticker(exchange_fxt, symbol))
    ticker = task.result()
    await asyncio.sleep(5.0)

    try:
        # Create order
        otoco = await otoco_manager_fxt.create_otoco(
            symbol,
            side=side,
            amount=amount,
            price=0.5 * ticker.low,
            tp_price=1.5 * ticker.high,
            sl_price=0.5 * ticker.low,
        )
        await asyncio.sleep(1.0)

        # Modify order
        target = copy(otoco)
        target.price = 0.7 * ticker.low
        await otoco_manager_fxt.modify_otoco(target)
        await asyncio.sleep(1.0)
        assert otoco_manager_fxt.get_otoco(otoco.id).price == pytest.approx(0.7 * ticker.low, rel=1e-3)

        # Fill order
        target = copy(otoco)
        target.price = 1.2 * ticker.high
        await otoco_manager_fxt.modify_otoco(target)
        start = asyncio.get_running_loop().time()
        await asyncio.sleep(1.0)
        print("f", datetime.now())
        while asyncio.get_running_loop().time() - start < 20.0:
            try:
                assert otoco_manager_fxt.get_order_per_otoco(otoco.id).status == "closed"
                assert otoco_manager_fxt.get_tp_order_per_otoco(otoco.id)
                assert otoco_manager_fxt.get_sl_order_per_otoco(otoco.id)
            except AssertionError as err:
                await asyncio.sleep(5.0)
                if asyncio.get_running_loop().time() - start >= 20.0:
                    raise err
            else:
                break
        print("fff", datetime.now())

        # Modify tp order
        target = copy(otoco)
        target.tp_price = 1.4 * ticker.high
        await otoco_manager_fxt.modify_otoco(target)
        await asyncio.sleep(5.0)
        assert otoco_manager_fxt.get_otoco(otoco.id).tp_price == pytest.approx(1.4 * ticker.high, rel=1e-3)

        # Modify sl order
        target = copy(otoco)
        target.sl_price = 0.6 * ticker.low
        await otoco_manager_fxt.modify_otoco(target)
        await asyncio.sleep(5.0)
        assert otoco_manager_fxt.get_otoco(otoco.id).sl_price == pytest.approx(0.6 * ticker.low, rel=1e-3)
    finally:
        pass
        # await order_manager_fxt.cancel_all_orders(symbol)

