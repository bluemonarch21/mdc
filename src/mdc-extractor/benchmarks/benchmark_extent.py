import random
import timeit

import numpy as np


def get_data():
    for _ in range(1_000_000):
        yield random.random()


np_data = np.fromiter(get_data(), float)


def max_min():
    data = list(get_data())
    return max(data), min(data)


def amax_amin():
    data = np.fromiter(get_data(), float)
    return np.amax(data), np.amin(data)


def for_loop():
    max_ = float("-inf")
    min_ = float("inf")
    for d in get_data():
        if d > max_:
            max_ = d
        if d < min_:
            min_ = d
    return max_, min_


if __name__ == "__main__":
    # 10 elements, 100000 times
    # max_min() 0.6920993
    # amax_amin() 1.7552806
    # for_loop() 0.4214546000000001  ***
    # 1,000,000 elements, 20 times
    # max_min() 4.3721934
    # amax_amin() 2.7295631          ***
    # for_loop() 3.4650418000000007
    print("max_min()", timeit.timeit("max_min()", "from __main__ import max_min", number=20))
    print("amax_amin()", timeit.timeit("amax_amin()", "from __main__ import amax_amin", number=20))
    print("for_loop()", timeit.timeit("for_loop()", "from __main__ import for_loop", number=20))
