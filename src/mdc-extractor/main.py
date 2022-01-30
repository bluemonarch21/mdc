import csv
from zipfile import ZipFile

from bs4 import BeautifulSoup

from constants import REPO
from musescore.next import newMuseScore

if __name__ == "__main__":
    rows = []
    zip_filepaths = list(
        sorted((REPO / "assets/musescore").glob("*.zip"), key=lambda a: int(a.stem))
    )
    for zfp in zip_filepaths:
        zfile = ZipFile(zfp)
        mscx_files = list(filter(lambda n: n.endswith(".mscx"), zfile.namelist()))
        if not mscx_files:
            print("errorrrrrr")
        openfile = zfile.open(mscx_files[0], "r")

        filename = mscx_files[0]
        print(zfp.stem, filename, "parsing")
        soup = BeautifulSoup(openfile, "xml")
        musescore = newMuseScore(soup)
        if musescore is not None:
            if musescore.get_piano_staffs():
                rh_avg_ps, lh_avg_ps = [staff.get_playing_speed() for staff in musescore.get_piano_staffs()]
                f = musescore.get_features()
                print(f"RHS.PS.avg={rh_avg_ps}",
                      f"LHS.PS.avg={lh_avg_ps}",
                      f"PE={f.PE}",
                      f"ANR={f.ANR}",
                      )

        continue

        version = soup.find("museScore").get("version")

        b_version = soup.find_all("programVersion")
        version_list = []
        for programVersion in b_version:
            if programVersion not in version_list:
                version_list.append(programVersion.text)
                # print(programVersion.text)

        # metatags = soup.find('museScore').find('Score').find_all('metaTag')
        # for tag in metatags:
        #     name = tag.get('name')
        #     text = tag.text
        #     dct = {
        #         'composer': 'metaTag:name=composer'
        #     }        #     data[dct[name]] = text

        num_accidental_notes = 0
        midi_num_occurrence = {}
        notes = soup.find_all("Note")
        for note in notes:
            # count midi numbers
            midi_num = note.find("pitch").text
            if midi_num in midi_num_occurrence:
                midi_num_occurrence[midi_num] += 1
            else:
                midi_num_occurrence[midi_num] = 1
            # count altered notes
            if note.find("Accidental") is not None:
                num_accidental_notes += 1
        PE = get_entropy(midi_num_occurrence)
        ANR = num_accidental_notes / len(notes)

        b_trackName = soup.find_all("trackName")
        instrument_list = []
        for instrument in b_trackName:
            if instrument not in instrument_list:
                instrument_list.append(instrument.text)
                # print(instrument.text)

        # print("--------------")

        b_tempo = soup.find_all("tempo")
        tempo_list = []
        for tempo in b_tempo:
            if tempo not in tempo_list:
                tempo_list.append(tempo.text)
                # print(tempo.text)

        # print("--------------")

        b_instrumentId = soup.find_all("instrumentId")
        instrumentId_list = []
        for instrumentId in b_instrumentId:
            if instrumentId not in instrumentId_list:
                instrumentId_list.append(instrumentId.text)
                # print(instrumentId.text)

        # TODO: Check for correct list (Piano, Grand Piano, keyboard.piano.[]
        piano = "Piano"
        hasPiano = False
        if piano in instrument_list:
            hasPiano = True
        else:
            hasPiano = False

        data = []
        data.append(zfp.stem)
        data.append(filename)
        data.append(version)
        data.append(version_list)
        data.append(instrument_list)
        data.append(tempo_list)
        data.append(instrumentId_list)
        data.append(hasPiano)
        data.append(PE)
        data.append(ANR)
        # print('data', data)
        rows.append(data)

    # print('done!')
    # print('rows', rows)

    Details = [
        "id",
        "filename",
        "version",
        "programVersion",
        "trackName",
        "Tempo",
        "IntrumentId",
        "hasPiano?",
        "PE",
        "ANR",
    ]
    with open("mdc.csv", "w", encoding="utf-8", newline="") as f:
        write = csv.writer(f)
        write.writerow(Details)
        write.writerows(rows)
