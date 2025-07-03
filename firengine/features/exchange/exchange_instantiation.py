import ccxt
import ccxt.pro as ccxt_pro

from firengine.lib.fire_enum import SupportedExchange
from firengine.utils.credential import get_user_password_keyring


def exchange_instance(ex_name: SupportedExchange, keyring_namespace: str) -> ccxt.Exchange:
    api_key, secret = get_user_password_keyring(keyring_namespace)
    config = {
        "apiKey": api_key,
        "secret": secret,
    }
    return getattr(ccxt, ex_name.name)(config)


def exchange_pro_instance(ex_name: SupportedExchange, keyring_namespace: str) -> ccxt_pro.Exchange:
    api_key, secret = get_user_password_keyring(keyring_namespace)
    config = {
        "apiKey": api_key,
        "secret": secret,
    }
    return getattr(ccxt_pro, ex_name.name)(config)
