import asyncio
import sys

import ccxt.pro as ccxt

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def watch_trades():
    exchange = ccxt.kraken({"newUpdates": True})
    symbol = "BTC/USD"
    print(exchange.options["tradesLimit"])
    while True:
        trades = await exchange.watch_trades(symbol)
        latest_trade = trades[-1]  # Get the latest trade
        print(len(trades))
        print(
            f"Time: {exchange.iso8601(latest_trade['timestamp'])} | Price: {latest_trade['price']} | Amount: {latest_trade['amount']} | Side: {latest_trade['side']}"
        )
    await exchange.close()


asyncio.run(watch_trades())
