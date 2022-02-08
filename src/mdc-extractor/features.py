import math
from typing import Any

from attr import define

from mathutils import round_to_significant
from musescore.proto import ProtoChord


def get_entropy(dct: dict[Any, int]) -> float:
    """Given a dict of [unique items, num occurrence], returns the entropy."""
    total = sum(dct.values())
    return -sum(v / total * math.log(v / total, 2) for v in dct.values())


def displacement_cost(c1: ProtoChord, c2: ProtoChord) -> int:
    a = [n.pitch for n in c1.notes]
    b = [n.pitch for n in c2.notes]
    d1 = max(a) - min(b)
    d2 = max(b) - min(a)
    d = max(d1, d2)
    if d >= 12:
        return 2
    if d >= 7:
        return 1
    return 0


@define
class Features:
    PS: tuple[float, float]  # playing speed
    PE: float  # pitch entropy
    DSR: float  # distinct stroke rate
    HDR: tuple[float, float]  # hand displacement rate
    HS: float  # hand stretch
    PPR: tuple[float, float]  # polyphony rate
    ANR: float  # altered note rate

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, float):
                kwargs[k] = round_to_significant(v, 5)
            elif isinstance(v, list):
                kwargs[k] = [round_to_significant(e, 5) for e in v]
        self.__attrs_init__(**kwargs)
