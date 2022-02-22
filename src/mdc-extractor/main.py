import csv
from pathlib import Path
from pprint import pprint
from typing import Any, Literal, Optional, Union
from zipfile import ZipFile

from bs4 import BeautifulSoup
from colorama import Fore, Style, init

from constants import REPO
from features import Features
from musescore import common
from musescore.next import newMuseScore

__all__ = ["open_and_extract"]

init()


def ask_yes_no(prompt: str) -> bool:
    while True:
        ans = input(f"{prompt} (y/N): ")
        if ans == "y":
            return True
        if ans == "N":
            return False


headers = [
    "id",
    "filename",
    "version",
    "programVersion",
    "PS_LH",
    "PS_RH",
    "PE",
    "DSR",
    "HDR_LH",
    "HDR_RH",
    "HS",
    "PPR_LH",
    "PPR_RH",
    "ANR",
    "title",
    "subtitle",
    "composer",
]


def open_and_extract(
    zfp: Path, *, throw: Union[bool, Literal["ask"]] = "ask", verbose: bool = True
) -> tuple[Optional[Features], Optional[list]]:
    zfile = ZipFile(zfp)
    mscx_files = list(filter(lambda n: n.endswith(".mscx"), zfile.namelist()))
    if not mscx_files:
        raise FileNotFoundError(zfile.namelist())
    filename = mscx_files[0]
    openfile = zfile.open(filename, "r")
    soup = BeautifulSoup(openfile, "xml")
    try:
        musescore = newMuseScore(soup)
        if musescore is not None:
            f = musescore.get_features()
            if f is not None:
                try:
                    print(
                        Fore.YELLOW + zfp.stem,
                        Fore.GREEN + filename,
                        Fore.CYAN + musescore.version,
                        Fore.GREEN + "√" + Style.RESET_ALL,
                        end=" ",
                    )
                    if verbose:
                        print(f, musescore.meta_info)
                    else:
                        print()
                    data = []
                    data.append(zfp.stem)
                    data.append(filename)
                    data.append(musescore.version)
                    data.append(musescore.programVersion)
                    data.append(f.PS[0])
                    data.append(f.PS[1])
                    data.append(f.PE)
                    data.append(f.DSR)
                    data.append(f.HDR[0])
                    data.append(f.HDR[1])
                    data.append(f.HS)
                    data.append(f.PPR[0])
                    data.append(f.PPR[1])
                    data.append(f.ANR)

                    info = musescore.meta_info

                    def func(dct: dict[str, Any], keys: list[str]) -> Any:
                        for key in keys:
                            if key in dct:
                                return dct[key]

                    data.append(func(info, ["workTitle", "Title"]))
                    data.append(func(info, ["Subtitle"]))
                    data.append(func(info, ["composer", "Composer"]))
                    assert len(data) == len(headers)
                    return f, data
                except IndexError:
                    return f, None
            else:
                print(
                    Fore.YELLOW + zfp.stem,
                    Fore.GREEN + filename,
                    Fore.CYAN + musescore.version,
                    Fore.YELLOW + "- not piano" + Style.RESET_ALL,
                )
        else:
            print(
                Fore.YELLOW + zfp.stem,
                Fore.GREEN + filename,
                Fore.CYAN + soup.find("museScore").get("version"),
                Fore.RED + "× no parser" + Style.RESET_ALL,
            )
    except Exception as e:
        print(
            Fore.YELLOW + zfp.stem,
            Fore.GREEN + filename,
            Fore.CYAN + soup.find("museScore").get("version"),
            Fore.RED + "× error while parsing" + Style.RESET_ALL,
        )
        if not throw:
            return None, None
        if throw == "ask":
            if ask_yes_no("continue?"):
                print(Fore.RED + str(e) + Style.RESET_ALL)
                input("Enter to continue...")
                return None, None
        raise
    return None, None


if __name__ == "__main__":
    rows = []
    zip_filepaths = list(
        sorted((REPO / "assets/musescore").glob("*.zip"), key=lambda a: int(a.stem))
    )
    for zfp in zip_filepaths:
        _, data = open_and_extract(zfp, throw=True)
        if data is not None:
            rows.append(data)

    print("done!")
    with open("_known_not_piano_values.txt", "w", encoding="utf-8") as f:
        pprint(common._known_not_piano_values, file=f)

    with open("mdc.csv", "w", encoding="utf-8", newline="") as f:
        write = csv.writer(f)
        write.writerow(headers)
        write.writerows(rows)
