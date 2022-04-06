from collections.abc import Iterable, Sequence
from itertools import tee, zip_longest
from typing import TypeVar

T = TypeVar('T')


def pairwise(iterable: Iterable[T]):
    # pairwise('ABCDEFG') --> AB BC CD DE EF FG
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def batch(sequence: Sequence[T], n: int = 1):
    # https://stackoverflow.com/questions/8290397/how-to-split-an-iterable-in-constant-size-chunks
    l = len(sequence)
    for ndx in range(0, l, n):
        yield sequence[ndx:min(ndx + n, l)]


def grouper(n: int, iterable: Iterable[T], fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(fillvalue=fillvalue, *args)
