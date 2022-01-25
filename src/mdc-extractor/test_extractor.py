import unittest

from constants import REPO

assets = REPO / "assets/musescore"

# muescore_Version: 1.14, 2.06, 3.01, 3.02
mscx_666_results = {
    "museScore:version": "1.14",
    "museScore.programVersion": "0.9.6.2",
    "museScore.Score.metaTag:name=arranger": "",  # version 2.06
    "museScore.Score.metaTag:name=composer": "",
    "museScore.Score.metaTag:name=creationDate": "",
    "museScore.Score.metaTag:name=lyricist": "",
    "museScore.Score.metaTag:name=movementNumber": "",
    "museScore.Score.metaTag:name=movementTitle": "",
    "museScore.Score.metaTag:name=workNumber": "",
    "museScore.Score.metaTag:name=workTitle": "",
    "museScore.Part[].Instrument.trackName": None,  # version 1.14
    "museScore.Part[].Instrument.instrumentId": None,  # version 2.06
    "museScore.tempolist:fix": 2,  # version 1.14
    "museScore.tempolist.relTempo": 84,  # version 1.14
    "museScore.tempolist.tempo": [{'text': '3.2', 'tick': 0}, {'text': '2.26667', 'tick': 17280}],  # version 1.14
    "museScore.Score.Staff[].Measure[].voice[].Tempo.tempo": '3.33333',  # version 2.06
    "museScore.Score.Staff[].Measure[].voice[].Tempo.text": 'sym>metNoteQuarterUp</sym> = 200',  # version 2.06
    "museScore.Score.Staff[].Measure[].voice[].Chord.durationType": '',  # version 1.14
    "museScore.Score.Staff[].Measure[].voice[].Chord.Note.pitch": '',  # version 1.14
    "museScore.Score.Staff[].Measure[].voice[].Chord.Note.tpc": '',  # version 1.14
    "museScore.Score.Staff[].Measure[].voice[].Chord.Note.Tie": '',  # version 2 (?) # marked in the first note in the tie group
    "museScore.Score.Staff[].Measure[].voice[].Rest": '',  # version
    "museScore.Score.Staff[].Measure[].voice[].Harmony.root": '',  # version ?? # 13-F,14 - C, 15 - G, 16-D, 17 - A, 18 - E, 19 - B
    "museScore.Score.Staff[].Measure[].voice[].Harmony.name": '',  # version ?? # m - minor, 7 - 7, '' (none) - major
    "museScore.Score.Staff[].Measure[].voice[].Harmony.base": '',  # version ?? # 17 - /A, 18 - /E
    "museScore.Score.Staff[].Measure[].voice[].KeySig": 1,  # version 1
    "museScore.Score.Staff[].Measure[].voice[].TimeSig": '',  # version 1
    "museScore.Score.Staff[].Measure[].voice[].KeySig.accidental": 1,  # version 3.01
    "museScore.Score.Staff[].Measure[].voice[].TimeSig.sigN": '',  # version 3.01
    "museScore.Score.Staff[].Measure[].voice[].TimeSig.sigD": '',  # version 3.01
    "text/Piano": None,
}



class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)  # add assertion here


if __name__ == '__main__':
    unittest.main()
