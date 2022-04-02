from collections.abc import Sequence
from typing import Callable, TypeVar

T = TypeVar("T")
U = TypeVar("U")


def bisect(arr: Sequence[T], e: T) -> tuple[int, int]:
    """Returns insertion index to remain in sorted order [left, right].

    Args:
        arr: sorted sequence
        e: element to find insertion index

    Reference:
        https://github.com/d3/d3-array#bisect

    Note:
        Try using https://docs.python.org/3/library/bisect.html first.

    Example:
        >>> bisect([1, 3, 5, 5, 10], 5)
        (2, 4)
        >>> bisect([1, 3, 5, 5, 10], 7)
        (4, 4)
        >>> bisect([1, 3, 5, 5, 10], 10)
        (4, 5)
        >>> bisect([1, 3, 5, 5, 10], 13)
        (5, 5)
        >>> bisect([1, 3, 5, 5, 10], 0)
        (0, 0)
        >>> bisect([1, 3], 0)
        (0, 0)
        >>> bisect([1, 3], 1)
        (0, 1)
        >>> bisect([1, 3], 2)
        (1, 1)
        >>> bisect([1], 0)
        (0, 0)
        >>> bisect([1], 1)
        (0, 1)
        >>> bisect([1], 2)
        (1, 1)
        >>> bisect([], 0)
        (0, 0)
    """
    new_left = True
    new_right = True
    left, right = 0, 0
    for i in range(len(arr)):
        if arr[i] < e:
            left = i
        if arr[i] >= e and new_left:
            left = i
            new_left = False
        if arr[i] == e:
            right = i
        if arr[i] > e and new_right:
            right = i
            new_right = False
    if arr:
        if arr[-1] < e:
            left = len(arr)
        if arr[-1] <= e:
            right = len(arr)
    return left, right


def find(arr: Sequence[T], c: U, hint: int, getter: Callable[[T], U] = None) -> T:
    """Returns e in sorted sequence `arr` that has value `c` from getter using `hint`.

    Args:
        arr: sorted sequence
        c: value to find
        hint: hint of index to start searching
        getter: callable to get value to compare element to c
    """
    if getter is None:
        getter = lambda x: x
    while 0 <= hint < len(arr):
        if getter(arr[hint]) == c:
            return arr[hint]
        elif getter(arr[hint]) > c:
            hint -= 1
        elif getter(arr[hint]) < c:
            hint += 1
    else:
        raise ValueError(f"value '{c}' is not in the sequence")
