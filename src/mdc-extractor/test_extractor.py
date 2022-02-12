import difflib
import sys
import unittest

from constants import REPO
from features import Features
from main import open_and_extract

expected_output = [
    (666, 1.14, Features(PS=[None, None], PE=4.0025, DSR=0.45361, HDR=[0.13125, 0.029412], HS=14.51, PPR=[0.074074, 0.043478], ANR=0)),
    (77075, 1.14, Features(PS=[0.29403, 0.17444], PE=5.6219, DSR=0.65937, HDR=[0.38067, 0.23004], HS=21.225, PPR=[0.30689, 0.017955], ANR=0.00062794)),
    (132879, 1.14, Features(PS=[0.29617, 0.23384], PE=5.0458, DSR=0.66509, HDR=[0.16606, 0.23185], HS=17.373, PPR=[0.030545, 0.0017953], ANR=0.00063796)),
    (169484, 1.14, Features(PS=[0.2749, 0.71864], PE=5.1598, DSR=0.58665, HDR=[0.30936, 0.37917], HS=22.634, PPR=[0.0080402, 0.42515], ANR=0)),
    (409606, 1.14, Features(PS=[0.45952, 0.74603], PE=4.9333, DSR=0.51429, HDR=[0.22452, 0.375], HS=18.914, PPR=[0.15287, 0.42021], ANR=0)),
    (525201, 1.14, Features(PS=[None, None], PE=2.9691, DSR=0.8456, HDR=[0.044944, 0.29839], HS=29.555, PPR=[0, 0.02669], ANR=0)),
    (718316, 1.14, Features(PS=[None, None], PE=4.6066, DSR=0.35714, HDR=[0.92466, 0.096386], HS=17.123, PPR=[0.64865, 0.077922], ANR=0)),
    (1095301, 2.06, Features(PS=[0.79605, 0.61467], PE=3.6036, DSR=0.18367, HDR=[0.058333, 0.30769], HS=25.06, PPR=[0, 0.3038], ANR=0)),
    (1495041, 2.06, Features(PS=[0.82323, 0.11693], PE=3.8205, DSR=0.55333, HDR=[0.035714, 0.21333], HS=30.486, PPR=[0, 0.15789], ANR=0.13934)),
    (2101001, 2.06, Features(PS=[1.4607, 0.82471], PE=4.8024, DSR=0.64147, HDR=[0.59914, 0.096882], HS=21.309, PPR=[0.55263, 0.12646], ANR=0.03148)),
    # TODO: Handle many piano?
    (4792423, 2.06, Features(PS=[0.3081, 0.45508, 0.44444, 0.43714, 0.29304], PE=3.8944, DSR=0.62614, HDR=[0.025411, 0.0051653, 0, 0.003006, 0.055818], HS=None, PPR=[0, 0, 0, 0, 0], ANR=0.0057409)),
    (5366272, 2.06, Features(PS=[None, None], PE=4.7626, DSR=0.62802, HDR=[0.20038, 0.18061], HS=22.797, PPR=[0.050193, 0.038023], ANR=0)),
    (5424388, 2.06, Features(PS=[0, 0], PE=None, DSR=0, HDR=[None, None], HS=None, PPR=[None, None], ANR=None)),
    (5460140, 2.06, Features(PS=[None, None], PE=1.5507, DSR=0.66839, HDR=[0.0098039, 0.42553], HS=22.774, PPR=[0, 0], ANR=0)),
    (5485521, 2.06, Features(PS=[0.46918, 0.4454], PE=4.3424, DSR=0.69697, HDR=[0.37452, 0.3028], HS=22.245, PPR=[0.038168, 0.62963], ANR=0.040189)),
]


class ExtractorTestCase(unittest.TestCase):
    def help_test(self, version):
        d = difflib.Differ()
        for expected in filter(lambda o: o[1] == version, expected_output):
            id_, _, ex_features = expected
            actual, _ = open_and_extract(REPO / f"assets/musescore/{id_}.zip", throw=True, verbose=False)
            with self.subTest(id=id_, version=version):
                try:
                    self.assertEqual(actual, ex_features)
                except AssertionError:
                    sys.stdout.writelines(d.compare([str(actual) + "\n"], [str(ex_features) + "\n"]))
                    raise

    def test_v114(self):
        self.help_test(1.14)

    def test_v206(self):
        self.help_test(2.06)

    def test_v301(self):
        self.help_test(3.01)

    def test_v302(self):
        self.help_test(3.02)


if __name__ == "__main__":
    unittest.main()
