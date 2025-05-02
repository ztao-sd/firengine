import asyncio

import ccxt
import ccxt.pro as ccxt_pro

from firengine.model.data_model import Order, PrivateTrade
from firengine.utils.credential import get_user_password_keyring


class AccountWatcher:
    def __init__(self, exchange: ccxt.Exchange, exchange_pro: ccxt_pro.Exchange):
        self._exchange = exchange
        self._exchange_pro = exchange_pro


if __name__ == "__main__":
    import json
    from pprint import pprint

    from firengine.features.exchange.exchange_utility import ExchangeUtility

    api_key, secret = get_user_password_keyring("bybit-demo")

    config = {
        "apiKey": api_key,
        "secret": secret,
    }
    exchange_ = ccxt.bybit(config)
    exchange_.enable_demo_trading(True)
    ex_pro = ccxt_pro.bybit(config)
    ex_pro.enable_demo_trading(True)

    ex_utils = ExchangeUtility(exchange_)

    symbols = ex_utils.get_symbols()
    print(symbols)

    # r = exchange_.fetch_balance()
    # pprint(r)
    ods = exchange_.fetch_open_orders()
    with open("bybit_orders.json", mode="w") as f:
        json.dump(ods, f)
    for od in ods:
        order = Order.from_kwargs(**od)
        pprint(order)
    # r = exchange_.fetch_my_trades("BTC/USDT")
    # pprint(r)
    # for od in exchange_.fetch_open_orders():
    #     order = Order.from_kwargs(**od)
    #     pprint(order)
    for tr in exchange_.fetch_my_trades("BTC/USDT:USDT"):
        trade = PrivateTrade.from_kwargs(**tr)
        pprint(trade)
    # r = exchange_.fetch_ledger()
    # pprint(len(r))
    # pprint(r)
    # order = exchange_.create_order(
    #     symbol="BTC/USDT:USDT",
    #     type="limit",
    #     side="buy",
    #     amount=0.5,
    #     price=50000.0,
    # )
    # order = exchange_.create_order(
    #     symbol="BTC/USDT:USDT",
    #     type="limit",
    #     side="sell",
    #     amount=0.5,
    #     price=150000.0,
    # )

    async def main():
        start = asyncio.get_event_loop().time()
        await ex_pro.fetch_closed_orders()
        print(asyncio.get_event_loop().time() - start)

    asyncio.run(main())
    account_watcher = AccountWatcher(exchange_, ex_pro)
