__all__ = [
    'get_bpm',
    'get_duration_type',
    'get_pulsation',
    'get_tick_length',
]


def get_bpm(value: float) -> float:
    """Returns Beats Per Minute value given floating value"""
    return round(value * 60, 2)


def get_dots_factor(dots: int) -> float:
    """Returns factor to multiply the pulsation of a note by.

    Example:
        >>> get_dots_factor(1)
        1.5
        >>> get_dots_factor(2)
        1.75
        >>> get_dots_factor(3)
        1.875
    """
    if dots > 0:
        return 0.5 ** dots + get_dots_factor(dots - 1)
    if dots == 0:
        return 1


_duration_type_pulsation = {
    'whole': 4,
    'half': 2,
    'quarter': 1,
    'eighth': 0.5,
    '16th': 0.25,
    '32nd': 0.125,
    '64th': 0.0625,
    '128th': 0.03125,
}


def get_pulsation(duration_type: str, dots: int = 0) -> float:
    """Returns pulsation value given durationType."""
    try:
        return _duration_type_pulsation[duration_type] * get_dots_factor(dots)
    except KeyError:
        raise ValueError(f'unknown duration_type: "{duration_type}"') from None


def get_tick_length(duration_type: str, dots: int = 0) -> int:
    x = get_pulsation(duration_type) * 480 * get_dots_factor(dots)
    return round(x)


_time_signature_duration_type = {
    1: 'whole',
    2: 'half',
    4: 'quarter',
    8: 'eighth',
    16: '16th',
    32: '32nd',
    64: '64th',
    128: '128th',
}


def get_duration_type(time_signature: int) -> str:
    """Returns durationType given time signature value"""
    try:
        return _time_signature_duration_type[time_signature]
    except KeyError:
        raise ValueError(f'unknown time_signature: "{time_signature}"') from None
