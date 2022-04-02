from typing import TypeVar, Union

KT = TypeVar("KT")
VT = TypeVar("VT")


def append_value(dct: dict[KT, Union[VT, list[VT]]], key: KT, value: VT) -> None:
    """ Add a value to a dict of list of values by key. """
    if key in dct:
        if isinstance(dct[key], list):
            dct[key].append(value)
        else:
            dct[key] = [dct[key], value]
    else:
        dct[key] = value
