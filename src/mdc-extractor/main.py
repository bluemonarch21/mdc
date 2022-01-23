import dataclasses
from pathlib import Path
from zipfile import ZipFile
from bs4 import BeautifulSoup


@dataclasses.dataclass
class Feature:
    PS: float  # playing speed
    PE: float  # pitch entropy
    DSR: float  # distinct stroke rate


def extract_feature(filename: str) -> Feature:
    pass


REPO = Path(__file__).resolve().parent.parent.parent
if __name__ == "__main__":
    for zfp in (REPO / "assets/musescore").glob("*.zip"):
        zfile = ZipFile(zfp)
        mscxfiles = list(filter(lambda n: n.endswith(".mscx"), zfile.namelist()))
        if not mscxfiles:
            print("errorrrrrr")
        openfile = zfile.open(mscxfiles[0], "r")

        print(mscxfiles[0])
        print(zfp)

        Bs_data = BeautifulSoup(openfile, "xml")
        b_staff = Bs_data.find_all('trackName')
        print(b_staff)

        b_name = Bs_data.find('Soprano')
        print(b_name)
        
        # Extracting the data stored in a
        # specific attribute of the
        # `child` tag
        # value = b_name.get('test')
        
        # print(value)

        break
