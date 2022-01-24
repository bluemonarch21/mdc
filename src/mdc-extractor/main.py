import dataclasses
import csv
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
    rows = []
    for zfp in (REPO / "assets/musescore").glob("*.zip"):
        zfile = ZipFile(zfp)
        mscxfiles = list(filter(lambda n: n.endswith(".mscx"), zfile.namelist()))
        if not mscxfiles:
            print("errorrrrrr")
        openfile = zfile.open(mscxfiles[0], "r")

        print(mscxfiles[0])
        print(zfp)

        Bs_data = BeautifulSoup(openfile, "xml")

        b_version = Bs_data.find_all('programVersion')
        version_list = []
        for version in b_version:
            if version not in version_list:
                version_list.append(version.text)
                print(version.text)

        b_trackName = Bs_data.find_all('trackName')
        instrument_list = []
        for instrument in b_trackName:
            if instrument not in instrument_list:
                instrument_list.append(instrument.text)
                print(instrument.text)

        print("--------------")

        b_tempo = Bs_data.find_all('tempo')
        tempo_list = []
        for tempo in b_tempo:
            if tempo not in tempo_list:
                tempo_list.append(tempo.text)
                print(tempo.text)

        print("--------------")

        b_instrumentId = Bs_data.find_all('instrumentId')
        instrumentId_list = []
        for instrumentId in b_instrumentId:
            if instrumentId not in instrumentId_list:
                instrumentId_list.append(instrumentId.text)
                print(instrumentId.text)

        piano = 'Piano'
        hasPiano = False
        if piano in instrument_list: 
            hasPiano = True
        else: hasPiano = False


        data = []
        data.append(version_list)
        data.append(instrument_list)
        data.append(tempo_list)
        data.append(instrumentId_list)
        data.append(hasPiano)
        print('data', data)
        rows.append(data)

    print('done!')
    print('rows', rows)

    Details = ['version', 'trackName', 'Tempo', 'IntrumentId', 'hasPiano?']  
    with open('mdc.csv', 'w') as f: 
        write = csv.writer(f) 
        write.writerow(Details) 
        write.writerows(rows) 