from attr import define

from musescore.proto import Chord
from utils.math import round_to_significant


def displacement_cost(c1: Chord, c2: Chord) -> int:
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
    PS: tuple[float, float]  # playing speed   # None if no tempo
    PE: float  # pitch entropy                 # None if no notes exist
    DSR: float  # distinct stroke rate         # None/NaN if both hand does not exist
    HDR: tuple[float, float]  # hand displacement rate  # None if no notes exist
    HS: float  # hand stretch                  # None/NaN if both hand does not exist
    PPR: tuple[float, float]  # polyphony rate # None if no notes exist
    ANR: float  # altered note rate            # None if no notes exist

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, float):
                kwargs[k] = round_to_significant(v, 5)
            elif isinstance(v, list):
                kwargs[k] = [round_to_significant(e, 5) for e in v]
        self.__attrs_init__(**kwargs)
