import logging

_debug_logger = logging.getLogger("debug")
_debug_logger.addHandler(logging.StreamHandler())
_debug_logger.setLevel(logging.DEBUG)


def debug(msg: object):
    _debug_logger.debug(msg)
