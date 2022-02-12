from typing import TypeVar

T = TypeVar("T")


def bisect(arr: list[T], e: T) -> tuple[int, int]:
    """Returns insertion index to remain in sorted order [left, right].

    Reference:
        https://github.com/d3/d3-array#bisect

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
