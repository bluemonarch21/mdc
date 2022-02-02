import random
import timeit

import numpy as np


def get_data():
    for _ in range(1_000):
        yield random.random()


np_data = np.fromiter(get_data(), float)


def average():
    return np.average(np.fromiter(get_data(), float))


def mean():
    return np.fromiter(get_data(), float).mean()


def sum_len():
    data = list(get_data())
    return sum(data) / len(data)


def for_loop():
    sum_ = 0
    count_ = 0
    for d in get_data():
        sum_ += d
        count_ += 1
    return sum_ / count_


if __name__ == "__main__":
    # elements 1,000,000 (lst), number 20
    # average() 3.1396532
    # mean() 2.7839158000000004     ***
    # sum_len() 3.3473655000000004
    # for_loop() 3.4704105999999992
    #
    # elements 1,000 (lst), number 10,000
    # average() 2.3594994000000002
    # mean() 1.5308909000000002
    # sum_len() 1.4205389999999998   ***
    # for_loop() 1.9745877999999992
    # average() 1.7903097
    # mean() 2.2587487
    # sum_len() 1.2301559000000006   ***
    # for_loop() 1.6132711999999998
    #
    # elements 1,000 (np.arr), number 10,000
    # average() 0.29302419999999996  *****
    # mean() 0.13606950000000007
    # sum_len() 1.2568222
    # for_loop() 1.7572254999999997
    print("average()", timeit.timeit("average()", "from __main__ import average", number=10000))
    print("mean()", timeit.timeit("mean()", "from __main__ import mean", number=10000))
    print("sum_len()", timeit.timeit("sum_len()", "from __main__ import sum_len", number=10000))
    print("for_loop()", timeit.timeit("for_loop()", "from __main__ import for_loop", number=10000))
