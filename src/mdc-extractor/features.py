import math

from attr import define


def get_entropy(dct: dict[any, int]) -> float:
    total = sum(dct.values())
    return -sum(v / total * math.log(v / total, 2) for v in dct.values())


@define
class Features:
    PS: float  # playing speed
    PE: float  # pitch entropy
    DSR: float  # distinct stroke rate
    ANR: float  # altered note rate
