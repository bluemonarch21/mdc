import csv
from typing import Any
from zipfile import ZipFile

from bs4 import BeautifulSoup

from constants import REPO
from musescore import v1, v2
from musescore.next import newMuseScore

if __name__ == "__main__":
    rows = []
    zip_filepaths = list(sorted((REPO / "assets/musescore").glob("*.zip"), key=lambda a: int(a.stem)))
    for zfp in zip_filepaths:
        zfile = ZipFile(zfp)
        mscx_files = list(filter(lambda n: n.endswith(".mscx"), zfile.namelist()))
        if not mscx_files:
            print("errorrrrrr")
        filename = mscx_files[0]
        openfile = zfile.open(filename, "r")
        try:
            soup = BeautifulSoup(openfile, "xml")
            musescore = newMuseScore(soup)
            if musescore is not None:
                f = musescore.get_features()
                if f:
                    try:
                        print(zfp.stem, filename, f, musescore.meta_info)
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
                        rows.append(data)
                    except IndexError:
                        pass
                else:
                    print(".")
            else:
                print(zfp.stem, filename, soup.find("museScore").get("version"))
            continue
        except Exception:
            print(zfp.stem, filename, "error while parsing")
            raise

    print("done!")
    print("v1 not piano names", v1.Part.known_not_piano_values)
    print("v2 not piano names", v2.Part.known_not_piano_values)
    Details = [
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

    with open("mdc.csv", "w", encoding="utf-8", newline="") as f:
        write = csv.writer(f)
        write.writerow(Details)
        write.writerows(rows)
