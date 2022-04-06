import functools
import itertools
import os
import pathlib
import typing

import pandas as pd


def load_henle_books(data_dir: pathlib.Path):
    df_books_headers = list(pd.read_csv(data_dir / "henle-books-header.csv").columns[:15]) + functools.reduce(lambda a, b: a + b, ([
            f'author{i+1}.Name',
            f'author{i+1}.Role',
            f'author{i+1}.URL',
        ] for i in range(9)))
    df_books = pd.read_csv(data_dir / "henle-books.csv", names=df_books_headers)
    itertools.chain(df_books.columns, [1])
    return df_books


if __name__ == '__main__':
    data_dir = pathlib.Path("D:\\data\\MDC")

    df_staff = pd.read_csv(data_dir / "henle-images-no-staff.csv")
    df_books = load_henle_books(data_dir)

