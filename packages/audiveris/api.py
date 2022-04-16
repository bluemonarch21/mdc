import asyncio
import functools
import logging
import os
import pathlib
import subprocess
import time
import typing
from copy import deepcopy

import chardet
import numpy as np
import pandas as pd
from lxml import etree

from utils import iter as iterutils


@functools.cache
def get_classpath(app_home: str):
    return str(pathlib.Path(app_home).resolve() / "lib/*")



def get_cmd(args: typing.Iterable[str]) -> str:
    return " ".join(args)


class Audiveris:
    def __init__(self, *, app_home: str, output_dir: str):
        # self.number = number
        self.app_home = app_home
        self.output_dir = output_dir

    @property
    def classpath(self) -> str:
        return get_classpath(self.app_home)

    def with_args(self, *args: str) -> list[str]:
        return ["java", "-cp", self.classpath, "Audiveris", *args]

    def help(self):
        return subprocess.run(self.with_args("-help"))

    def has_staffs(self, input_files: list[str]):
        stdout = subprocess.check_output(self.with_args(
            "-batch",
            "-output", self.output_dir,
            "-step", "SCALE",
            "--", *input_files,
        ))
        s = stdout.decode()
        filenames = [pathlib.Path(file).stem for file in input_files]
        output = {filename: 1 for filename in filenames}
        for line in s.splitlines():
            # WARN  []                      Main 382  | Exception on 0000, java.lang.RuntimeException: Could not find file "D:\data\MDC\henle\0001\w1500\0000.jpg"
            # WARN  [0001]                 SheetStub 344  | 0001 Too large interline value: 396 pixels This sheet does not seem to contain staff lines.
            # WARN  [0016]                 SheetStub 344  | 0016 With an interline value of 7 pixels, either this sheet contains no staves, or the picture resolution is too low (try 300 DPI).
            # WARN  [0167]                 SheetStub 344  | 0167 Too few staff filaments: 0 This sheet does not seem to contain staff lines.
            # WARN  [0176]                 SheetStub 344  | 0176 Too few black pixels: 0.0000% This sheet is almost blank.
            # WARN  [0060]              ScaleBuilder 276  | No reliable beam height found, guessed value: 8
            if line.startswith(f"WARN"):
                for filename in filenames:
                    if f"[{filename}]" in line:
                        if "Too large interline value" in line and "This sheet does not seem to contain staff lines." in line:
                            output[filename] = 0
                        elif "With an interline value of" in line and "either this sheet contains no staves, or the picture resolution is too low" in line:
                            output[filename] = 0
                        elif "Too few staff filaments" in line and "This sheet does not seem to contain staff lines." in line:
                            output[filename] = 0
                        elif "Too few black pixels" in line and "This sheet is almost blank." in line:
                            output[filename] = 0
                        elif "ScaleBuilder" in line and "No reliable beam height found" in line:
                            logging.info(line)
                        else:
                            logging.warning(line)
                            print(line)
                        break
                else:
                    logging.error(line)
                    print(line)
        return output

    def export_mxl_args(self, input_files: list[str]) -> list[str]:
        # utf-16
        return self.with_args(
            "-batch",
            "-output", self.output_dir,
            "-export",
            "--", *input_files,
        )

    def export_mxl_cmd(self, input_files: list[str]) -> str:
        return get_cmd(self.export_mxl_args(input_files))

    # @staticmethod
    # def process_export_mxl_output(stdout: bytes):
    #     try:
    #         s = stdout.decode(encoding='utf-16')
    #     except UnicodeDecodeError:
    #         encoding = chardet.detect(stdout)
    #         logging.warning(f"detected encoding '{encoding}'")
    #         try:
    #             s = stdout.decode(encoding=encoding)
    #         except UnicodeDecodeError:
    #             raise
    #     # filenames = [pathlib.Path(file).stem for file in input_files]
    #     # output = {filename: 1 for filename in filenames}  # TODO: check from Audiveris logs
    #     for line in s.splitlines():
    #         # WARN  []                      Main 382  | Exception on 0000, java.lang.RuntimeException: Could not find file "D:\data\MDC\henle\0001\w1500\0000.jpg"
    #         if line.startswith(f"WARN"):
    #             for filename in filenames:
    #                 if f"[{filename}]" in line:
    #                     logging.warning(line)
    #                     print(line)
    #                     break
    #             else:
    #                 logging.error(line)
    #                 print(line)
    #         elif line.startswith(f"ERROR") or line.startswith(f"FATAL"):
    #             logging.error(line)
    #             print(line)
    #     # return output

    def get_playlist(self, input_files: list[str]):
        playlist = etree.Element("play-list")
        sheets_selection_1 = etree.Element("sheets-selection")
        sheets_selection_1.text = "1"
        for input_file in input_files:
            excerpt = etree.SubElement(playlist, "excerpt")
            path = etree.SubElement(excerpt, "path")
            path.text = input_file
            excerpt.append(deepcopy(sheets_selection_1))
        s = etree.tostring(playlist, pretty_print=True)
        if isinstance(s, bytes):
            s = s.decode()
        return f'<?xml version="1.0" ?>\n{s}'

    def save_playlist(self, filename: typing.Union[str, pathlib.Path], input_files: list[str]):
        s = self.get_playlist(input_files)
        with open(filename, 'w') as f:
            f.write(s)

    def export_playlist_args(self, playlist_path: str):
        return self.with_args(
            "-batch",
            "-output", self.output_dir,
            "-playlist", playlist_path,
            "-save",
        )


async def run(program, *args):
    proc = await asyncio.create_subprocess_exec(
        program,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    return proc, stdout, stderr


def process_staffs(app_home: str, output_dir: str, data_dir: pathlib.Path, *, load_previous: bool = False, skip_under: int = 1):
    if load_previous:
        df = pd.read_csv("henle-images-no-staff.csv")
    else:
        df = pd.DataFrame([], columns=['hn', 'page', 'has_staff'])

    for hn_path in (data_dir / "henle").glob("*"):
        hn = hn_path.stem
        if int(hn) < skip_under:
            continue

        print(f"HN {hn} started {time.asctime()}")
        start_time = time.time_ns()
        out = Audiveris(app_home=app_home, output_dir=f"{output_dir}\\{hn:0>4}").has_staffs([str(p) for p in (hn_path / 'w1500').glob("*.jpg")])
        elapsed = time.time_ns() - start_time
        print(f"HN {hn} processed {len(out.keys()):>3} pages, {sum(out.values()):>3} notes ({elapsed // (10**9) // 60} minutes {elapsed // (10**9) % 60} seconds)")

        for page, has_staff in out.items():
            df.loc[df.shape[0]] = {'hn': hn, 'page': page, 'has_staff': has_staff}

        start_time = time.time_ns()
        df.to_csv("henle-images-no-staff.csv", index=False)
        elapsed = time.time_ns() - start_time
        print(f"HN {hn} saved to `henle-images-no-staff.csv` ({elapsed} nanoseconds)")


async def export_mxl_worker(name: int, queue: asyncio.Queue, result: asyncio.Queue):
    while True:
        hn, i, batch, args = await queue.get()

        print(f"INFO\t\t[{name}] HN {hn} batch #{i} starting...\t\t\ttime is {time.asctime()}")
        # print(f"DEBUG\t\t[{name}] HN {hn} batch #{i} {to_cmd(args)}")
        start_time = time.time_ns()
        proc, stdout, stderr = await run(*args)
        elapsed = time.time_ns() - start_time
        result.put_nowait((hn, i, batch, proc.returncode))
        if proc.returncode == 0:
            # TODO: do something with stdout
            print(f"INFO\t\t[{name}] HN {hn} batch #{i} ({','.join(map(str, batch))}) exported ??? files "
                  f"({elapsed // (10 ** 9) // 60} minutes {elapsed // (10 ** 9) % 60} seconds) [{elapsed / len(batch) // (10 ** 9)} seconds per file]")
        else:
            print(f"ERROR\t\t[{name}] HN {hn} batch #{i} ({','.join(map(str, batch))})")
            logging.error(args)
            logging.error(stderr.decode())
            # logging.error(stdout.decode())

        queue.task_done()


async def export_mxl_result_worker(result: asyncio.Queue, *, data_dir: pathlib.Path = None):
    if data_dir is None:
        df = pd.DataFrame([], columns=['hn', 'page', 'exported'])
    else:
        df = pd.read_csv(data_dir / "henle-images-exported.csv")

    while True:
        hn, i, batch, returncode = await result.get()

        if returncode == 0:
            for page in batch:
                df.loc[df.shape[0]] = {'hn': hn, 'page': page, 'exported': 1}
        else:
            for page in batch:
                df.loc[df.shape[0]] = {'hn': hn, 'page': page, 'exported': 0}
        start_time = time.time_ns()
        df.to_csv(data_dir / "henle-images-exported.csv", index=False)
        elapsed = time.time_ns() - start_time
        print(f"DEBUG\t\t[x] HN {hn} batch #{i} (return: {returncode}) saved to `henle-images-exported.csv` ({elapsed} nanoseconds)")

        result.task_done()


async def export_mxl_async(app_home: str, output_dir: str, data_dir: pathlib.Path, *, batch_size: int = 10, num_workers: int = 4, max_qsize: int = 4, load: bool = True, use_omr: bool = True):
    df_staff = pd.read_csv(data_dir / "henle-images-no-staff.csv")
    if load:
        df_exported = pd.read_csv(data_dir / "henle-images-exported.csv")
    else:
        df_exported = pd.DataFrame([], columns=['hn', 'page', 'exported'])
    # merge so we can just use one DataFrame filter
    df = df_staff.merge(df_exported, how='left', on=['hn', 'page']).set_index(['hn', 'page'])

    queue = asyncio.Queue()
    result = asyncio.Queue()

    worker_tasks = []
    for i in range(num_workers):
        task = asyncio.create_task(export_mxl_worker(i + 1, queue, result))
        worker_tasks.append(task)
    record_task = asyncio.create_task(export_mxl_result_worker(result, data_dir=data_dir if load else None))

    for hn_path in (data_dir / "henle").glob("*"):
        hn = hn_path.stem
        audiveris = Audiveris(app_home=app_home, output_dir=f"{output_dir}\\{hn:0>4}")

        x = df.loc[int(hn)]
        for i, batch in enumerate(iterutils.batch(x[(x['has_staff'] == 1) & (x['exported'] != 1)].index, batch_size)):
            jpg_files = [f"{data_dir}\\henle\\{hn:0>4}\\w1500\\{page:0>4}.jpg" for page in batch]  # use jpg
            omr_files = [f"{output_dir}\\{hn:0>4}\\{page:0>4}\\{page:0>4}.omr" for page in batch]  # use omr
            if not use_omr:
                # Need to purge old files else Audiveris can bug and get stuck
                for f in omr_files:
                    try:
                        os.remove(f)
                    except FileNotFoundError:
                        pass
            args = audiveris.export_mxl_args(input_files=jpg_files)
            queue.put_nowait((hn, i + 1, batch, args))
            # print(f"DEBUG\t\t[] HN {hn} batch #{i} ({','.join(map(str, batch))}) added to queue")
            while queue.qsize() >= max_qsize:  # wait if qsize is too big
                print(f"....\t\t[] sleeping... ({queue.qsize()} items in queue)\t\ttime is {time.asctime()}")
                await asyncio.sleep(60)
    await queue.join()
    for task in worker_tasks:
        task.cancel()
    await result.join()
    record_task.cancel()
    await asyncio.gather(*worker_tasks, record_task, return_exceptions=True)


def export_mxl(app_home: str, output_dir: str, data_dir: pathlib.Path, *, use_omr: bool = True, start_at: int = 1, end_at: int = float('inf')):
    seconds_per_page = np.fromiter([], int)
    df_staff = pd.read_csv(data_dir / "henle-images-no-staff.csv")
    df_indexed = df_staff.set_index(['hn', 'page'])

    for hn_path in (data_dir / "henle").glob("*"):
        hn = hn_path.stem
        if int(hn) < start_at or int(hn) > end_at:
            continue
        audiveris = Audiveris(app_home=app_home, output_dir=f"{output_dir}\\{hn:0>4}")

        x: pd.DataFrame = df_indexed.loc[int(hn)]
        pages = x[x['has_staff'] == 1].index

        if len(pages) == 0:
            print(f"ERROR\t\t[] HN {hn} has no notes pages, skipping")
            continue

        if use_omr:
            omr_files = [f"{output_dir}\\{hn:0>4}\\{page:0>4}\\{page:0>4}.omr" for page in pages]  # use omr
            args = audiveris.export_mxl_args(input_files=omr_files)
        else:  # should run on new folder
            jpg_files = [f"{data_dir}\\henle\\{hn:0>4}\\w1500\\{page:0>4}.jpg" for page in pages]  # use jpg
            args = audiveris.export_mxl_args(input_files=jpg_files)

        print(f"INFO\t\t[] HN {hn} starting... time is {time.asctime()} (ETA is {'???' if seconds_per_page.size == 0 else time.ctime(time.time() + np.percentile(seconds_per_page, 70, overwrite_input=True))})")
        start_time = time.time_ns()
        proc = subprocess.run(args, capture_output=True)
        elapsed = time.time_ns() - start_time
        seconds_per_page = np.append(seconds_per_page, elapsed / len(pages) // (10 ** 9))
        if proc.returncode == 0:
            # s = proc.stdout.decode(encoding=chardet.detect(proc.stdout).get('encoding') or 'windows-1252')
            # INFO [0073]                 Book 1820 | Scores built: 3
            # INFO [0073]      PartwiseBuilder 2172 | Exporting sheet(s): [#1]
            # INFO [0073]        ScoreExporter 92   | Score 0073.mvt1 exported to D:\data\MDC\audiveris\1408\0073\0073.mvt1.mxl
            # INFO [0073]      PartwiseBuilder 2172 | Exporting sheet(s): [#1]
            # INFO [0073]        ScoreExporter 92   | Score 0073.mvt2 exported to D:\data\MDC\audiveris\1408\0073\0073.mvt2.mxl
            # INFO [0073]      PartwiseBuilder 2172 | Exporting sheet(s): [#1]
            # INFO [0073]        ScoreExporter 92   | Score 0073.mvt3 exported to D:\data\MDC\audiveris\1408\0073\0073.mvt3.mxl
            # INFO [0073]                 Book 2056 | Stored /book.xml
            # INFO [0073]                 Book 2002 | Book stored as D:\data\MDC\audiveris\1408\0073\0073.omr
            # TODO: do sth with stdout
            print(f"INFO\t\t[] HN {hn} processed {len(pages):>3} pages, ??? exported"
                  f" ({elapsed // (10**9) // 60} minutes {elapsed // (10**9) % 60} seconds) [{seconds_per_page[-1]} seconds per file]")
            # print(s.replace('\n', '\\n'))
        else:
            print(f"ERROR\t\t[] HN {hn} (code: {proc.returncode})")
            stdout = proc.stdout.decode(encoding=chardet.detect(proc.stdout).get('encoding') or 'windows-1252')
            print(stdout)
            logging.debug(stdout)
            stderr = proc.stderr.decode(encoding=chardet.detect(proc.stderr).get('encoding') or 'utf-16')
            print(stderr)
            logging.error(stderr)

        start_time = time.time_ns()
        df_exported = get_df_exported(output_dir)
        df_exported.to_csv(data_dir / "henle-images-exported.csv", index=False)
        elapsed = time.time_ns() - start_time
        print(f"INFO\t\t[] HN {hn} saved to `henle-images-exported.csv` ({elapsed} nanoseconds)")


def get_df_exported(output_dir: str) -> pd.DataFrame:
    df = pd.DataFrame([], columns=['hn', 'page', 'num_mxl'])
    top_path = pathlib.Path(output_dir)
    for hn_path in top_path.glob("*"):
        if not hn_path.is_dir():
            continue
        hn = hn_path.stem
        print(hn, end='')
        for page_path in hn_path.glob("*"):
            if not page_path.is_dir():
                continue
            page = page_path.stem
            df.loc[df.shape[0]] = {'hn': hn, 'page': page, 'num_mxl': sum(1 for _ in page_path.glob("*.mxl"))}
            print('.', end='')
        print()
    return df


def save_compound_book(app_home: str, output_dir: str, *, start_at: int = 1, end_at: int = float('inf')):
    s_start_time = time.time_ns()
    df = pd.read_csv(data_dir / "henle-images-exported.csv")
    df_indexed = df[df["num_mxl"] == 1].set_index(["hn", "page"])

    ns_per_page = np.fromiter([], int)
    for hn in df_indexed.groupby(['hn']).indices.keys():
        if hn < start_at or hn > end_at:
            continue
        # audiveris = Audiveris(app_home=app_home, output_dir=f"{output_dir}\\{hn:0>4}")
        audiveris = Audiveris(app_home=app_home, output_dir=f"{data_dir}\\playlists\\{hn:0>4}")

        pages = df_indexed.loc[hn].index
        print(f"INFO\t\t[] HN {hn} starting... time is {time.asctime()} (ETA is {'???' if ns_per_page.size == 0 else time.ctime(time.time() + np.percentile(ns_per_page, 70, overwrite_input=True)/(10 ** 9))})")
        start_time = time.time_ns()
        omr_files = [f"{output_dir}\\{hn:0>4}\\{page:0>4}\\{page:0>4}.omr" for page in pages]
        tmp = f"{data_dir}\\playlists\\{hn:0>4}.xml"
        audiveris.save_playlist(tmp, input_files=omr_files)
        print(f"INFO\t\t[] saved {tmp}")
        args = audiveris.export_playlist_args(tmp)
        proc = subprocess.run(args, timeout=5*60)
        elapsed = time.time_ns() - start_time

        ns_per_page = np.append(ns_per_page, elapsed / len(pages))
        if proc.returncode == 0:
            # INFO  []                      Book 1485 | Loading book D:\data\MDC\audiveris\0002\0165\0165.omr
            # INFO  []                  PlayList 113  | BookExcerpt{0008 spec:1}
            # INFO  []                  PlayList 129  |    Processing Stub#1
            # INFO  []                  PlayList 147  | Copying tree from D:\data\MDC\audiveris\0002\0164\0164.omr/sheet#1 to D:\data\MDC\playlists\0002.omr/sheet#125
            # INFO  []                  PlayList 113  | BookExcerpt{0165 spec:1}
            # INFO  []                  PlayList 129  |    Processing Stub#1
            # INFO  []                  PlayList 147  | Copying tree from D:\data\MDC\audiveris\0002\0165\0165.omr/sheet#1 to D:\data\MDC\playlists\0002.omr/sheet#126
            # INFO  []                      Book 2056 | Stored /book.xml
            # INFO  []                  PlayList 182  | Compound book created as D:\data\MDC\playlists\0002.omr
            # stdout = proc.stdout.decode(encoding=chardet.detect(proc.stdout).get('encoding') or 'windows-1252')
            # for line in stdout.splitlines():
            #     if 'Compound book created' in line:
            #         print(line)
            print(f"INFO\t\t[] HN {hn} processed {len(pages):>3} pages, ??? exported"
                  f" ({elapsed // (10**9) // 60} minutes {elapsed // (10**9) % 60} seconds) [{ns_per_page[-1] // (10 ** 6)} ms per page]")
        else:
            print(f"ERROR\t\t[] HN {hn} (code: {proc.returncode})")
            # stdout = proc.stdout.decode(encoding=chardet.detect(proc.stdout).get('encoding') or 'windows-1252')
            # print(stdout)
            # logging.debug(stdout)
            # stderr = proc.stderr.decode(encoding=chardet.detect(proc.stderr).get('encoding') or 'utf-16')
            # print(stderr)
            # logging.error(stderr)
    print(f"\n"
          f"Tasked finished at {time.asctime()}\n"
          f"elapsed: {(time.time_ns() - s_start_time) // 10**9} s\n"
          f"total books: {len(ns_per_page)}\n"
          f"total time: {np.sum(ns_per_page) // 10**9} s\n"
          f"median+ time: {np.percentile(ns_per_page, 60, overwrite_input=True) // (10 ** 6)} ms per page\n"
          f"average time: {np.mean(ns_per_page) // (10 ** 6)} ms per page")


def export_book(app_home: str, *, start_at: int = 1, end_at: int = float('inf')):
    s_start_time = time.time_ns()
    df = pd.read_csv(data_dir / "henle-images-exported.csv")
    df_indexed = df[df["num_mxl"] == 1].set_index(["hn", "page"])

    ns_per_book = np.fromiter([], int)
    for hn in df_indexed.groupby(['hn']).indices.keys():
        if hn < start_at or hn > end_at:
            continue
        audiveris = Audiveris(app_home=app_home, output_dir=f"{data_dir}\\playlists")
        omr_file = f"{data_dir}\\playlists\\{hn:0>4}.omr"

        print(f"INFO\t\t[] HN {hn} starting... time is {time.asctime()} (ETA is {'???' if ns_per_book.size == 0 else time.ctime(time.time() + np.percentile(ns_per_book, 70, overwrite_input=True) / 10 ** 9)})")
        start_time = time.time_ns()
        args = audiveris.export_mxl_args(input_files=[omr_file])
        proc = subprocess.run(args, timeout=20*60)
        elapsed = time.time_ns() - start_time

        ns_per_book = np.append(ns_per_book, elapsed)
        if proc.returncode == 0:
            s = (f"INFO\t\t[] HN {hn} processed, {len(list((pathlib.Path(data_dir)/'playlists').glob(f'{hn:0>4}.*.mxl'))):>3} exported"
                 f" ({elapsed // (10**9) // 60} minutes {elapsed // (10**9) % 60} seconds)")
            print(s)
            logging.info(s)
        else:
            s = (f"ERROR\t\t[] HN {hn} (code: {proc.returncode})")
            print(s)
            logging.error(s)
    elapsed = time.time_ns() - s_start_time
    print(f"\n"
          f"Tasked finished at {time.asctime()}\n"
          f"elapsed: {elapsed // (10**9) // 60} minutes {elapsed // (10**9) % 60} seconds\n"
          f"total books: {len(ns_per_book)}\n"
          f"total time: {np.sum(ns_per_book) // 10**9} s\n"
          f"median+ time: {np.percentile(ns_per_book, 60, overwrite_input=True) // (10 ** 9)} s per book\n"
          f"average time: {np.mean(ns_per_book) // (10 ** 9)} s per book")


if __name__ == '__main__':
    app_home = "D:\\Program Files\\Audiveris"
    data_dir = pathlib.Path("D:\\data\\MDC")
    output_dir = "D:\\data\\MDC\\audiveris"

    logging.basicConfig(filename=f"audiveris.book.{time.strftime('%m-%d.%H-%M-%S')}.log", level=logging.DEBUG)

    # process_staffs(app_home, output_dir, data_dir)
    # asyncio.run(export_mxl_async(app_home, output_dir, data_dir, batch_size=5, num_workers=1, max_qsize=1, load=False, use_omr=False))
    # export_mxl(app_home, output_dir, data_dir, use_omr=False, start_at=9423, end_at=9423)
    # export_mxl(app_home, output_dir, data_dir, use_omr=False, start_at=1491)
    # save_compound_book(app_home, output_dir, start_at=650)
    # export_book(app_home, start_at=560)
