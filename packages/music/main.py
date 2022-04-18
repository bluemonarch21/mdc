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
    batch_size = 8

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
    del df_books
    del df_mxl_man
    # print(df.columns)
    print(df.shape)
    # print(df.loc[0])

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

    dfi = pd.DataFrame([], columns=['hn', 'title'])
    # new batch
    count = 0
    batch_number = 1
    ds = features.DataSet(classLabel='ClassLabel')
    ds.addFeatureExtractors(feature_extractors)
    for i, row in df.iterrows():
        print(f'>>> {row["mvt1"][:-4]}')
        zfp = data_dir / "playlists" / row['mvt1']
        zfp = zfp.with_suffix('.mxl')
        # zf = zipfile.ZipFile(zfp)
        # assert row['mvt1'] in zf.namelist()
        # f = zf.open(row['mvt1'])
        # s = converter.parse(f.read())
        try:
            s = converter.parse(str(zfp))
        except Exception as e:
            if isinstance(row['mvt2'], str) and row['mvt2']:
                zfp = data_dir / "playlists" / row['mvt2']
                zfp = zfp.with_suffix('.mxl')
                try:
                    s = converter.parse(str(zfp))
                except Exception as e:
                    if isinstance(row['mvt3'], str) and row['mvt3']:
                        zfp = data_dir / "playlists" / row['mvt3']
                        zfp = zfp.with_suffix('.mxl')
                        try:
                            s = converter.parse(str(zfp))
                        except Exception as e:
                            print(e)
                            continue
                    else:
                        print(e)
                        continue
            else:
                print(e)
                continue
        ds.addData(s)
        dfi.loc[dfi.shape[0]] = row
        count += 1
        print(f'>>> {count}!')
        if count >= batch_size:
            # process batch
            print(">>> processing...")
            ds.process()
            ds.write(str(data_dir / f"henle-music21-{batch_number}x{batch_size}.csv"))
            print(f"Exported henle-music21-{batch_number}x{batch_size}.csv")
            dfi.to_csv(data_dir / "henle-music21-info.csv")
            print(dfi.shape)
            # new batch
            count = 0
            batch_number += 1
            ds = features.DataSet(classLabel='ClassLabel')
            ds.addFeatureExtractors(feature_extractors)
    if count > 0:
        # process batch
        print(">>> processing...")
        ds.process()
        ds.write(str(data_dir / f"henle-music21-{batch_number}x{batch_size}.csv"))
        print(f"Exported henle-music21-{batch_number}x{batch_size}.csv")
        dfi.to_csv(data_dir / "henle-music21-info.csv")
        print(dfi.shape)
