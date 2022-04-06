import asyncio
import functools
import logging
import os
import pathlib
import subprocess
import time
import typing

import chardet
import pandas as pd

from utils import iter as iterutils

logging.basicConfig(filename=f"audiveris.export.{time.strftime('%m-%d.%H-%M-%S')}.log", level=logging.DEBUG)


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
            # WARN  [0176]                 SheetStub 344  | 0176 Too few black pixels: 0.0000% This sheet is almost blank.
            # WARN  [0060]              ScaleBuilder 276  | No reliable beam height found, guessed value: 8
            if line.startswith(f"WARN"):
                for filename in filenames:
                    if f"[{filename}]" in line:
                        if "Too large interline value" in line and "This sheet does not seem to contain staff lines." in line:
                            output[filename] = 0
                        elif "With an interline value of" in line and "either this sheet contains no staves, or the picture resolution is too low" in line:
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
        # print(f"DEBUG\t\t[{name}] HN {hn} batch #{i} {args}")
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


async def export_mxl(app_home: str, output_dir: str, data_dir: pathlib.Path, *, batch_size: int = 10, num_workers: int = 4, max_qsize: int = 4, load: bool = True, use_omr: bool = True):
    df_staff = pd.read_csv(data_dir / "henle-images-no-staff.csv")
    try:
        df_exported = pd.read_csv(data_dir / "henle-images-exported.csv")
    except FileNotFoundError:
        df_exported = pd.DataFrame([], columns=['hn', 'page', 'exported'])
    df = df_staff.merge(df_exported, how='left', on=['hn', 'page']).set_index(['hn', 'page'])

    queue = asyncio.Queue()
    result = asyncio.Queue()

    worker_tasks = []
    for i in range(num_workers):
        task = asyncio.create_task(export_mxl_worker(i + 1, queue, result))
        worker_tasks.append(task)
    record_task = asyncio.create_task(export_mxl_result_worker(result, data_dir=data_dir if load else None))

    try:
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
                while queue.qsize() > max_qsize:  # wait if qsize is too big
                    print(f"....\t\t[] sleeping... ({queue.qsize()} items in queue)\ttime is {time.asctime()}")
                    await asyncio.sleep(60)
    except KeyboardInterrupt:
        pass
    finally:
        await queue.join()
        for task in worker_tasks:
            task.cancel()
        await result.join()
        record_task.cancel()
        await asyncio.gather(*worker_tasks, record_task, return_exceptions=True)


if __name__ == '__main__':
    app_home = "D:\\Program Files\\Audiveris"
    data_dir = pathlib.Path("D:\\data\\MDC")
    output_dir = "D:\\data\\MDC\\audiveris"

    # process_staffs(app_home, output_dir, data_dir)
    asyncio.run(export_mxl(app_home, output_dir, data_dir, batch_size=5, num_workers=4, load=False, use_omr=False))
