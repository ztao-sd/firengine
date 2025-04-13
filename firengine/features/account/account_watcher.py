import ccxt
import ccxt.pro as ccxt_pro

from firengine.utils.credential import get_user_password_keyring


class AccountWatcher:
    def __init__(self, exchange: ccxt.Exchange, exchange_pro: ccxt_pro.Exchange):
        self._exchange = exchange
        self._exchange_pro = exchange_pro


if __name__ == "__main__":
    from pprint import pprint
    api_key, secret = get_user_password_keyring("bybit-demo")

    config = {
        "apiKey": api_key,
        "secret": secret,
    }
    exchange_ = ccxt.bybit(config)
    exchange_.enable_demo_trading(True)
    exchange_pro_ = ccxt_pro.bybit(config)
    exchange_pro_.enable_demo_trading(True)

    # r = exchange_.fetch_balance()
    # pprint(r)
    r = exchange_.fetch_closed_orders()
    pprint(r)

    account_watcher = AccountWatcher(exchange_, exchange_pro_)
