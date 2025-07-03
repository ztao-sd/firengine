import logging

from pythonjsonlogger.orjson import OrjsonFormatter

from firengine.lib.common_type import StrPath


def setup_standard_structured_logging(level: int, filename: StrPath | None = None, verbose: bool = False):
    logger = logging.getLogger()
    logger.setLevel(level)

    formatter = OrjsonFormatter("%(timestamp) %(levelname)s %(message)s", timestamp=True)

    # Stream handler
    if verbose:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        handler.setLevel(level)
        logger.addHandler(handler)

    if filename is not None:
        handler = logging.FileHandler(filename)
        handler.setFormatter(formatter)
        handler.setLevel(level)
        logger.addHandler(handler)
