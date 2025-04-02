import time

import ccxt

kraken = ccxt.kraken()

symbol = "BTC/USD"

while True:
    ticker = kraken.fetch_ticker(symbol)
    print(f"Price: {ticker['last']}, Time: {ticker['datetime']}")
    time.sleep(1)  # Adjust polling rate as needed
