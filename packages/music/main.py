import asyncio
import difflib
import functools
import heapq
import itertools
import logging
import os
import pathlib
import subprocess
import time
import typing
import zipfile
from copy import deepcopy

import chardet
import numpy as np
import pandas as pd
from lxml import etree
from music21 import converter, features

from utils import iter as iterutils

if __name__ == '__main__':
    data_dir = pathlib.Path("D:\\data\\MDC")
    limit = 1000

    df_books_headers = list(pd.read_csv(data_dir / "henle-books-header.csv").columns[:15]) + functools.reduce(
        lambda a, b: a + b, ([
            f'author{i + 1}.Name',
            f'author{i + 1}.Role',
            f'author{i + 1}.URL',
        ] for i in range(9)))
    df_books = pd.read_csv(data_dir / "henle-books.csv", names=df_books_headers, na_values='nil')

    df_mxl_man = pd.read_csv(data_dir / "henle-mxl-manual - henle-mxl-manual.csv")
    df_mxl_man = df_mxl_man[df_mxl_man['title'].notna()]
    df_mxl_man_no_problem = df_mxl_man['problem'] == 0
    df_mxl_man_problem_fixed = (df_mxl_man['problem'] == 1) & (df_mxl_man['changed'] == 1)
    df_mxl_man = df_mxl_man[df_mxl_man_no_problem | df_mxl_man_problem_fixed]
    print(df_mxl_man.shape)

    df_books['title'] = df_books['detail.Title']
    df_books['hn'] = df_books['book.HN']

    df = df_mxl_man.join(df_books.set_index(['hn', 'title']), on=['hn', 'title'], how='left')
    print(df.columns)
    print(df.shape)
    # print(df.loc[0])

    # [<class 'music21.features.jSymbolic.InitialTimeSignatureFeature'>, <class 'music21.features.jSymbolic.CompoundOrSimpleMeterFeature'>, <class 'music21.features.jSymbolic.TripleMeterFeature'>, <class 'music21.features.jSymbolic.QuintupleMeterFeature'>, <class 'music21.features.jSymbolic.ChangesOfMeterFeature'>, <class 'music21.features.jSymbolic.MostCommonPitchPrevalenceFeature'>, <class 'music21.features.jSymbolic.MostCommonPitchClassPrevalenceFeature'>, <class 'music21.features.jSymbolic.RelativeStrengthOfTopPitchesFeature'>, <class 'music21.features.jSymbolic.RelativeStrengthOfTopPitchClassesFeature'>, <class 'music21.features.jSymbolic.IntervalBetweenStrongestPitchesFeature'>, <class 'music21.features.jSymbolic.IntervalBetweenStrongestPitchClassesFeature'>, <class 'music21.features.jSymbolic.NumberOfCommonPitchesFeature'>, <class 'music21.features.jSymbolic.PitchVarietyFeature'>, <class 'music21.features.jSymbolic.PitchClassVarietyFeature'>, <class 'music21.features.jSymbolic.RangeFeature'>, <class 'music21.features.jSymbolic.MostCommonPitchFeature'>, <class 'music21.features.jSymbolic.PrimaryRegisterFeature'>, <class 'music21.features.jSymbolic.ImportanceOfBassRegisterFeature'>, <class 'music21.features.jSymbolic.ImportanceOfMiddleRegisterFeature'>, <class 'music21.features.jSymbolic.ImportanceOfHighRegisterFeature'>, <class 'music21.features.jSymbolic.MostCommonPitchClassFeature'>, <class 'music21.features.jSymbolic.BasicPitchHistogramFeature'>, <class 'music21.features.jSymbolic.PitchClassDistributionFeature'>, <class 'music21.features.jSymbolic.FifthsPitchHistogramFeature'>]
    feature_extractors = features.extractorsById([
        'r31',  # music21.features.jSymbolic.InitialTimeSignatureFeature
        'r32',  # music21.features.jSymbolic.CompoundOrSimpleMeterFeature
        'r33',  # music21.features.jSymbolic.TripleMeterFeature
        'r34',  # music21.features.jSymbolic.QuintupleMeterFeature
        'r35',  # music21.features.jSymbolic.ChangesOfMeterFeature
        'p1',   # music21.features.jSymbolic.MostCommonPitchPrevalenceFeature
        'p2',   # music21.features.jSymbolic.MostCommonPitchClassPrevalenceFeature
        'p3',   # music21.features.jSymbolic.RelativeStrengthOfTopPitchesFeature
        'p4',   # music21.features.jSymbolic.RelativeStrengthOfTopPitchClassesFeature
        'p5',   # music21.features.jSymbolic.IntervalBetweenStrongestPitchesFeature`
        'p6',   # music21.features.jSymbolic.IntervalBetweenStrongestPitchClassesFeature
        'p7',   # music21.features.jSymbolic.NumberOfCommonPitchesFeature
        'p8',   # music21.features.jSymbolic.PitchVarietyFeature
        'p9',   # music21.features.jSymbolic.PitchClassVarietyFeature
        'p10',  # music21.features.jSymbolic.RangeFeature
        'p11',  # music21.features.jSymbolic.MostCommonPitchFeature
        'p12',  # music21.features.jSymbolic.PrimaryRegisterFeature
        'p13',  # music21.features.jSymbolic.ImportanceOfBassRegisterFeature
        'p14',  # music21.features.jSymbolic.ImportanceOfMiddleRegisterFeature
        'p15',  # music21.features.jSymbolic.ImportanceOfHighRegisterFeature
        'p16',  # music21.features.jSymbolic.MostCommonPitchClassFeature
        'p19',  # music21.features.jSymbolic.BasicPitchHistogramFeature
        'p20',  # music21.features.jSymbolic.PitchClassDistributionFeature
        'p21',  # music21.features.jSymbolic.FifthsPitchHistogramFeature
    ])
    ds = features.DataSet(classLabel='Composer')
    ds.addFeatureExtractors(feature_extractors)

    count = 0
    for i, row in df.iterrows():
        zfp = data_dir / "playlists" / row['mvt1']
        zfp = zfp.with_suffix('.mxl')
        # zf = zipfile.ZipFile(zfp)
        # assert row['mvt1'] in zf.namelist()
        # f = zf.open(row['mvt1'])
        # s = converter.parse(f.read())
        s = converter.parse(str(zfp))
        ds.addData(s)
        count += 1
        if count >= limit:
            break

    ds.process()
    ds.write(str(data_dir / f"henle-music21.csv"))
    print('exported CSV')
    df.to_csv(data_dir / "henle-features-info.csv")
