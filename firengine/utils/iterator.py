from collections.abc import Iterator
from itertools import tee


def peek[T](iterator: Iterator[T]) -> T:
    [forked] = tee(iterator, 1)
    return next(forked)