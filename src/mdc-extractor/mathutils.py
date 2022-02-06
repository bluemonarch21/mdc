import math


def round_to_significant(x: float, n: int) -> float:
    """

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
