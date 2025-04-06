import time
from datetime import datetime


def time_ms() -> int:
    return time.time_ns() // 1_000_000


def dt_to_time_ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def parse_timeframe_to_ms(timeframe: str) -> int:
    amount = int(timeframe[0:-1])
    unit = timeframe[-1]
    if "y" == unit:
        scale = 60 * 60 * 24 * 365
    elif "M" == unit:
        scale = 60 * 60 * 24 * 30
    elif "w" == unit:
        scale = 60 * 60 * 24 * 7
    elif "d" == unit:
        scale = 60 * 60 * 24
    elif "h" == unit:
        scale = 60 * 60
    elif "m" == unit:
        scale = 60
    elif "s" == unit:
        scale = 1
    else:
        raise RuntimeError(f"timeframe unit {unit} is not supported")
    return amount * scale * 1000

