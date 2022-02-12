import math
from typing import Any


def round_to_significant(x: float, n: int) -> float:
    """Returns `x` rounded to `n` significant digits.

    Examples:
        >>> round_to_significant(4/3, 3)
        1.33
        >>> round_to_significant(-50/3, 5)
        -16.667
        >>> round_to_significant(0, 5)
        0
    """
    if x is None:
        return None
    if x == 0:
        return 0
    if math.isnan(x):
        return x
    return round(x, -int(math.floor(math.log10(abs(x)))) + (n - 1))


def get_entropy(dct: dict[Any, int]) -> float:
    """Given a dict of [unique items, num occurrence], returns the entropy."""
    total = sum(dct.values())
    return -sum(v / total * math.log(v / total, 2) for v in dct.values())
