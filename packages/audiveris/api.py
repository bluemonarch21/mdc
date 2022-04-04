# import contextlib
# import datetime
import functools
# import io
import logging
import pathlib
# import re
import subprocess
import time
# import typing

import pandas as pd

logging.basicConfig(filename=f"audiveris.scale.{time.strftime('%m-%d.%H-%M-%S')}.log", level=logging.DEBUG)


@functools.cache
def get_classpath(app_home: str):
    return str(pathlib.Path(app_home).resolve() / "lib/*")


class Audiveris:
    def __init__(self, *, app_home: str, output_dir: str):
        self.app_home = app_home
        self.output_dir = output_dir

    @property
    def classpath(self) -> str:
        return get_classpath(self.app_home)

    def with_args(self, *args: str):
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
                            logging.debug(line)
                            print(line)
                        break
                else:
                    logging.error(line)
                    print(line)
        return output


if __name__ == '__main__':
    app_home = "D:\\Program Files\\Audiveris"
    output_dir = "D:\\data\\MDC\\audiveris"
    load_previous = False
    skip_under = 1

    if load_previous:
        df = pd.read_csv("henle-images-no-staff.csv")
    else:
        df = pd.DataFrame([], columns=['hn', 'page', 'has_staff'])

    for hn_path in pathlib.Path("D:\\data\\MDC\\henle").glob("*"):
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
