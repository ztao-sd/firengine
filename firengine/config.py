from dataclasses import dataclass
from pathlib import Path

HOME_DIR = Path.home()
CRYPTO_DATA_DIR = HOME_DIR / "crypto-data"
KRAKEN_OHLCVT_DATA_DIR = CRYPTO_DATA_DIR / "Kraken_OHLCVT"
KRAKEN_TRADES_DATA_DIR = CRYPTO_DATA_DIR / "Kraken_Trading_History"

@dataclass
class Config:
    supported_exchanges = []
