import asyncio
import difflib
import functools
import heapq
import itertools
import logging
import math
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
from matplotlib import pyplot as plt
from music21 import converter, features


def batch_process(data_dir: pathlib.Path, *, batch_size: int = 8):
    df_mxl_man = pd.read_csv(data_dir / "henle-mxl-manual-v3.csv")
    df_mxl_man = df_mxl_man[df_mxl_man['difficulty'].notna()]
    df_mxl_man_no_problem = df_mxl_man['problem'] == 0
    df_mxl_man_problem_fixed = (df_mxl_man['problem'] == 1) & (df_mxl_man['changed'] == 1)
    df = df_mxl_man[df_mxl_man_no_problem | df_mxl_man_problem_fixed]
    print(df.shape)
    # print(df.loc[0])

    feature_extractors = features.extractorsById([
        'm1',    # MelodicIntervalHistogramFeature
        'm2',    # AverageMelodicIntervalFeature
        'm3',    # MostCommonMelodicIntervalFeature
        'm4',    # DistanceBetweenMostCommonMelodicIntervalsFeature
        'm5',    # MostCommonMelodicIntervalPrevalenceFeature
        'm6',    # RelativeStrengthOfMostCommonIntervalsFeature
        'm7',    # NumberOfCommonMelodicIntervalsFeature
        'm8',    # AmountOfArpeggiationFeature
        'm9',    # RepeatedNotesFeature
        'm10',   # ChromaticMotionFeature
        'm11',   # StepwiseMotionFeature
        'm12',   # MelodicThirdsFeature
        'm13',   # MelodicFifthsFeature
        'm14',   # MelodicTritonesFeature
        'm15',   # MelodicOctavesFeature
        'm17',   # DirectionOfMotionFeature
        'm18',   # DurationOfMelodicArcsFeature
        'm19',   # SizeOfMelodicArcsFeature
        'r15',   # NoteDensityFeature
        'r17',   # AverageNoteDurationFeature
        'r18',   # VariabilityOfNoteDurationFeature
        'r19',   # MaximumNoteDurationFeature
        'r20',   # MinimumNoteDurationFeature
        'r21',   # StaccatoIncidenceFeature
        'r22',   # AverageTimeBetweenAttacksFeature
        'r23',   # VariabilityOfTimeBetweenAttacksFeature
        'r24',   # AverageTimeBetweenAttacksForEachVoiceFeature
        'r25',   # AverageVariabilityOfTimeBetweenAttacksForEachVoiceFeature
        'r30',   # InitialTempoFeature
        'r31',   # InitialTimeSignatureFeature
        'r32',   # CompoundOrSimpleMeterFeature
        'r35',   # ChangesOfMeterFeature
        'r36',   # DurationFeature
        'p1',    # MostCommonPitchPrevalenceFeature
        'p2',    # MostCommonPitchClassPrevalenceFeature
        'p3',    # RelativeStrengthOfTopPitchesFeature
        'p4',    # RelativeStrengthOfTopPitchClassesFeature
        'p5',    # IntervalBetweenStrongestPitchesFeature
        'p6',    # IntervalBetweenStrongestPitchClassesFeature
        'p7',    # NumberOfCommonPitchesFeature
        'p8',    # PitchVarietyFeature
        'p9',    # PitchClassVarietyFeature
        'p10',   # RangeFeature
        'p11',   # MostCommonPitchFeature
        'p12',   # PrimaryRegisterFeature
        'p13',   # ImportanceOfBassRegisterFeature
        'p14',   # ImportanceOfMiddleRegisterFeature
        'p15',   # ImportanceOfHighRegisterFeature
        'p16',   # MostCommonPitchClassFeature
        'p19',   # BasicPitchHistogramFeature
        'p20',   # PitchClassDistributionFeature
        'p21',   # FifthsPitchHistogramFeature
        'k1',    # TonalCertainty
        'ql1',   # UniqueNoteQuarterLengths
        'ql2',   # MostCommonNoteQuarterLength
        'ql3',   # MostCommonNoteQuarterLengthPrevalence
        'ql4',   # RangeOfNoteQuarterLengths
        'cs1',   # UniquePitchClassSetSimultaneities
        'cs2',   # UniqueSetClassSimultaneities
        'cs3',   # MostCommonPitchClassSetSimultaneityPrevalence
        'cs4',   # MostCommonSetClassSimultaneityPrevalence
        'cs5',   # MajorTriadSimultaneityPrevalence
        'cs6',   # MinorTriadSimultaneityPrevalence
        'cs7',   # DominantSeventhSimultaneityPrevalence
        'cs8',   # DiminishedTriadSimultaneityPrevalence
        'cs9',   # TriadSimultaneityPrevalence
        'cs10',  # DiminishedSeventhSimultaneityPrevalence
        'cs11',  # IncorrectlySpelledTriadPrevalence
        'cs12',  # ChordBassMotionFeature
        'mc1',   # LandiniCadence
    ])

    feature_extractors += [features.extractorsById('p22', library=['native'])]

    dfi = pd.DataFrame([], columns=['hn', 'title', 'difficulty'])
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
        ds.addData(s, classValue=row['difficulty'])
        dfi.loc[dfi.shape[0]] = row
        count += 1
        print(f'>>> {count}!')
        if count >= batch_size:
            # process batch
            print(">>> processing...")
            ds.process()
            ds.write(str(data_dir / f"henle-music21-{batch_number}x{batch_size}.tab"))
            print(f"Exported henle-music21-{batch_number}x{batch_size}.tab")
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
        ds.write(str(data_dir / f"henle-music21-{batch_number}x{batch_size}.tab"))
        print(f"Exported henle-music21-{batch_number}x{batch_size}.tab")
        dfi.to_csv(data_dir / "henle-music21-info.csv", index=False)
        print(dfi.shape)


def merge_batches(data_dir: pathlib.Path, *, batch_size: int):
    dfi = pd.read_csv(data_dir / "henle-music21-info.csv")
    df_ds = None
    for i in range(math.ceil(dfi.shape[0] / batch_size)):
        batch_number = i + 1
        print(batch_number)
        df_dsi = pd.read_csv(data_dir / f"henle-music21-{batch_number}x{batch_size}.tab", skiprows=[1, 2], dialect='excel-tab')
        if df_ds is None:
            df_ds = df_dsi
        else:
            df_ds = pd.concat([df_ds, df_dsi], ignore_index=True, sort=False)

    df = dfi.merge(df_ds, left_index=True, right_index=True)
    print(df)
    df.to_csv(data_dir / "henle-music21.csv", index=False)


if __name__ == '__main__':
    # data_dir = pathlib.Path("D:\\data\\MDC")
    # batch_process(pathlib.Path("D:\\data\\MDC"), batch_size=8)
    merge_batches(pathlib.Path("D:\\data\\MDC"), batch_size=8)

    # df_books_headers = list(pd.read_csv(data_dir / "henle-books-header.csv").columns[:15]) + functools.reduce(
    #     lambda a, b: a + b, ([
    #         f'author{i + 1}.Name',
    #         f'author{i + 1}.Role',
    #         f'author{i + 1}.URL',
    #     ] for i in range(9)))
    # df_books = pd.read_csv(data_dir / "henle-books.csv", names=df_books_headers, na_values='nil')
    #
    # df_mxl_man = pd.read_csv(data_dir / "henle-mxl-manual-v2.csv")
    # print(df_mxl_man.shape)
    #
    # df_books['title'] = df_books['detail.Title']
    # df_books['hn'] = df_books['book.HN']
    #
    # df = df_mxl_man.join(df_books.set_index(['hn', 'title']), on=['hn', 'title'], how='left')
    # del df_books
    # del df_mxl_man
    # print(df.groupby('detail.HenleDifficulty').describe())

    # df_mxl_man = pd.read_csv(data_dir / "henle-mxl-manual-v3.csv")
    # df_mxl_man = df_mxl_man[df_mxl_man['difficulty'].notna()]
    # df_mxl_man_no_problem = df_mxl_man['problem'] == 0
    # df_mxl_man_problem_fixed = (df_mxl_man['problem'] == 1) & (df_mxl_man['changed'] == 1)
    # df_mxl_man = df_mxl_man[df_mxl_man_no_problem | df_mxl_man_problem_fixed]
    # print(df_mxl_man['difficulty'].value_counts())

    # df[['hn', 'title', 'detail.HenleDifficulty']].to_csv(data_dir / "henle-mxl-manual-pad.csv")
