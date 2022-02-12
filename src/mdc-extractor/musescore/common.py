from collections.abc import Iterable, Iterator, Sequence
from functools import reduce
from itertools import chain, islice

from features import Features
from musescore.proto import Measure, Part, Staff
from utils.arr import find
from utils.math import get_entropy


def get_features(*staffs: Staff) -> Features:
    avg_pitches = []
    PS = []
    HDR = []
    PPR = []
    for staff in staffs:
        avg_pitches.insert(0, staff.get_average_pitch())
        PS.insert(0, staff.get_playing_speed())
        HDR.insert(0, staff.get_hand_displacement_rate())
        PPR.insert(0, staff.get_polyphony_rate())
    HS = None if len(list(filter(lambda x: x is not None, avg_pitches))) != 2 else abs(avg_pitches[1] - avg_pitches[0])

    num_accidental_notes = 0
    midi_num_occurrence = {}
    count = 0
    for note in chain.from_iterable([staff.notes for staff in staffs]):
        # count midi numbers
        if note.pitch in midi_num_occurrence:
            midi_num_occurrence[note.pitch] += 1
        else:
            midi_num_occurrence[note.pitch] = 1
        # count altered notes
        if note.accidental is not None:
            num_accidental_notes += 1
        count += 1
    PE = None if count == 0 else get_entropy(midi_num_occurrence)
    ANR = None if count == 0 else num_accidental_notes / count

    DSR = get_distinct_stroke_rate(*staffs)
    return Features(PS=PS, PE=PE, DSR=DSR, HDR=HDR, HS=HS, PPR=PPR, ANR=ANR)


def _a_intersect_stroke_ticks(a: set[int], b: Measure):
    return a.intersection(b.stroke_ticks)


def _union_stroke_ticks(a: set[int], b: Measure):
    return a.union(b.stroke_ticks)


def _get_measures(s: Staff):
    return s.measures


def get_distinct_stroke_rate(*staffs: Staff) -> float:
    """
    Returns 1 minus rate of common strokes. Only well-defined for 2 staffs.

    Currently, "common" means present in all staffs.
    To count rate of strokes present only in one staff,
    use a generalized version of numpy.setxor1d() instead.
    """
    if len(staffs) < 1:
        raise ValueError("there must be at least one staff")
    intersection = 0
    union = 0
    for measures in zip(*map(_get_measures, staffs)):
        measures: tuple[Measure, ...]
        intersection += len(reduce(_a_intersect_stroke_ticks, islice(measures, 1, None), measures[0].stroke_ticks))
        union += len(reduce(_union_stroke_ticks, islice(measures, 1, None), measures[0].stroke_ticks))
    return 1 - intersection / union


def get_staffs_from_piano_parts_id(parts: Iterable[Part], staffs: Sequence[Staff]) -> Iterator[Staff]:
    for part in parts:
        if part.is_piano:
            for s in part.staffs:
                try:
                    yield find(staffs, s.id, s.id - 1, lambda e: e.id)
                except ValueError:
                    # could not find piano staff with specified id
                    pass


_known_piano_values: set[str] = {
    "piano",
    "grand piano",
    "keyboard",
    "pno.",
    "ピアノ",
    "keyboard.piano",
    "keyboard.harpsichord",
}
_known_not_piano_values: set[str] = set()


def _found_value_in_obj(obj, not_found_memo: list[str], *attrs: str) -> bool:
    for attr in attrs:
        if hasattr(obj, attr):
            val = getattr(obj, attr)
            if not val:
                continue
            val = val.lower()
            if val in _known_piano_values:
                return True
            not_found_memo.append(val)
    return False


def is_piano(part: Part) -> bool:
    values = []
    if _found_value_in_obj(part, values, "name", "trackName"):
        return True
    if _found_value_in_obj(part.instrument, values, "instrumentId", "trackName", "longName", "shortName"):
        return True
    _known_not_piano_values.update(values)
    return False
