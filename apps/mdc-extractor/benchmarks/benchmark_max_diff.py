import random
import timeit
from itertools import zip_longest

import numpy as np


def grouper(iterable, n, fillvalue):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def get_data():
    for d in (random.randint(0, 127) for _ in range(50_000)):
        lst = []
        for _ in range(random.randint(1, 5)):
            lst.append(d)
        yield lst


data = list(grouper(get_data(), 2, fillvalue=1))


def extent(lst: list):
    max_ = float("-inf")
    min_ = float("inf")
    for d in lst:
        if d > max_:
            max_ = d
        if d < min_:
            min_ = d
    return max_, min_


def for_loop():
    for a, b in data:
        maxa, mina = extent(a)
        maxb, minb = extent(b)
        diff1 = maxa - minb
        diff2 = maxb - mina
        diff = max(diff1, diff2)
    return diff


def max_min():
    for a, b in data:
        diff1 = max(a) - min(b)
        diff2 = max(b) - min(a)
        diff = max(diff1, diff2)
    return diff


def amax_amin():
    for a, b in data:
        a = np.array(a)
        b = np.array(b)
        diff1 = np.amax(a) - np.amin(b)
        diff2 = np.amax(b) - np.amin(a)
        diff = max(diff1, diff2)
    return diff


def broadcast():
    for a, b in data:
        a = np.array(a)
        b = np.array(b)
        diff = np.amax(np.abs(np.hsplit(a, len(a)) - b))
    return diff


if __name__ == "__main__":
    # elements 50,000, inner list <= 5, number 20
    # for_loop() 1.0192326
    # max_min() 0.5325466999999999   ***
    # amax_amin() 10.8377656
    # broadcast() 17.2567363
    print("for_loop()", timeit.timeit("for_loop()", "from __main__ import for_loop", number=20))
    print("max_min()", timeit.timeit("max_min()", "from __main__ import max_min", number=20))
    print("amax_amin()", timeit.timeit("amax_amin()", "from __main__ import amax_amin", number=20))
    print("broadcast()", timeit.timeit("broadcast()", "from __main__ import broadcast", number=20))
