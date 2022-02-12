import csv
from pathlib import Path
from typing import Any, Literal, Optional, Union
from zipfile import ZipFile

from bs4 import BeautifulSoup
from colorama import Fore, Style, init

from constants import REPO
from musescore import v1, v2
from musescore.next import newMuseScore

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


def open_and_extract(zfp: Path, *, throw: Union[bool, Literal["ask"]] = "ask") -> Optional[list]:
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
                        Style.RESET_ALL + str(f),
                        musescore.meta_info,
                    )
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
                    return data
                except IndexError:
                    return None
            else:
                print(".")
        else:
            print(
                Fore.YELLOW + zfp.stem,
                Fore.GREEN + filename,
                Fore.CYAN + soup.find("museScore").get("version") + Style.RESET_ALL,
            )
    except Exception as e:
        print(
            Fore.YELLOW + zfp.stem,
            Fore.GREEN + filename,
            Fore.CYAN + soup.find("museScore").get("version"),
            Fore.RED + "error while parsing" + Style.RESET_ALL,
        )
        if not throw:
            return None
        if throw == "ask":
            if ask_yes_no("continue?"):
                print(Fore.RED + str(e) + Style.RESET_ALL)
                input("Enter to continue...")
                return None
        raise


if __name__ == "__main__":
    rows = []
    zip_filepaths = list(sorted((REPO / "assets/musescore").glob("*.zip"), key=lambda a: int(a.stem)))
    for zfp in zip_filepaths:
        data = open_and_extract(zfp, throw=True)
        if data is not None:
            rows.append(data)

    print("done!")
    # print("v1 not piano names", v1.Part.known_not_piano_values)
    # print("v2 not piano names", v2.Part.known_not_piano_values)

    with open("mdc.csv", "w", encoding="utf-8", newline="") as f:
        write = csv.writer(f)
        write.writerow(headers)
        write.writerows(rows)
