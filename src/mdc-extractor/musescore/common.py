from functools import reduce
from itertools import chain, islice

from features import Features
from musescore.proto import Measure, Staff
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
