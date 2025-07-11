import os.path
from dataclasses import dataclass
from pathlib import Path

HOME_DIR = Path.home()
ENGINE_DATA_DIR = HOME_DIR / "firengine_data"
KRAKEN_OHLCVT_DATA_DIR = ENGINE_DATA_DIR / "Kraken_OHLCVT"
LOG_DIR = ENGINE_DATA_DIR / "log"

for dir_ in (ENGINE_DATA_DIR, LOG_DIR):
    if not os.path.exists(dir_):
        os.makedirs(dir_, exist_ok=True)

# Old stuff
CRYPTO_DATA_DIR = HOME_DIR / "crypto-data"
KRAKEN_TRADES_DATA_DIR = CRYPTO_DATA_DIR / "Kraken_Trading_History"

# Constants
SECONDS_PER_YEAR = 31_536_000


@dataclass
class Config:
    supported_exchanges = []
