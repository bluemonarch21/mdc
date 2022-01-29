from typing import ClassVar, Optional, Union

import bs4.element
from bs4 import BeautifulSoup

from attrs import define
from musescore import v1


def newMuseScore(soup: BeautifulSoup) -> Union[v1.MuseScore, None]:
    museScore_tag = soup.find("museScore")
    version = museScore_tag.get("version")
    if version in v1.MuseScore.known_versions:
        return v1.MuseScore.from_tag(museScore_tag)
    else:
        return None


# @define
# class MuseScore:
#     # attributes
#     version: str
#
#     # child elements
#     programVersion: str
#     programRevision: str
#     siglist: Optional[list["sig"]]  # v1.14 only
#     tempolist: Optional[list["tempo"]]  # v1.14 only
#     Part: list["Part"]  # v1.14 only
#     Staff: list["Staff"]  # v1.14 only
#
#     # class variables
#     known_versions: ClassVar[list[str]] = ["1.14", "2.06", "3.01", "3.02", "301"]
#
#     @classmethod
#     def from_soup(cls, soup: BeautifulSoup) -> "MuseScore":
#         museScore_tag = soup.find("museScore")
#         assert museScore_tag is not None
#
#         version = museScore_tag.get("version")
#         if version not in cls.known_versions:
#             raise ValueError(f"found unknown version: {version}")
#         programVersion = museScore_tag.find("programVersion").text
#         programRevision = museScore_tag.find("programRevision").text
#
#         siglist_tag = museScore_tag.find("siglist")
#         siglist = (
#             None
#             if siglist_tag is None
#             else list(map(sig.from_tag, museScore_tag.find("siglist").find_all("sig")))
#         )
#         tempolist_tag = museScore_tag.find("tempolist")
#         tempolist = (
#             None
#             if tempolist_tag is None
#             else list(
#                 map(tempo.from_tag, museScore_tag.find("tempolist").find_all("tempo"))
#             )
#         )
#
#         return cls(version, programVersion, programRevision, siglist, tempolist)
#
#
# @define
# class Score:
#     arranger: str
#     composer: str
#     creationDate: str
#     lyricist: str
#     movementNumber: str
#     movementTitle: str
#     workNumber: str
#     workTitle: str
#     Part: list["Part"]
#     Staff: list["Staff"]
#
#     @property
#     def feature_playing_speed(self):
#         for part in self.Part:
#             for staff in part.Staff:
#                 for measure in staff.Measure:
#                     for v in measure.voice:
#                         v.Tempo
#
#
# @define
# class Part:
#     Staff: list["Staff"]
#     trackName: str
#     Instrument: "Instrument"
#
#
# @define
# class Instrument:
#     longName: str  # long name used to label parts on the 1st page
#     shortName: str  # short name used to label parts from 2nd page
#     trackName: str  # English name of the track?
#     instrumentId: str  # id of the instrument, e.g. keyboard.piano.grand
#     Articulation: list["Articulation"]
#
#     # channels: list['Channel']  # MIDI info for channels (?)
#
#     @define
#     class Articulation:
#         """museScore.Score.Part.Instrument.Articulation"""
#
#         # TODO: record known articulation names (these increase the difficulty of a piece)
#         name: str  # e.g. staccato, tenuto, marcato
#         velocity: int  # loudness (can go up beyond 100)
#         gateTime: int  # 0-100 how long the sound lasts
#
#
# @define
# class Staff:
#     id: int
#     defaultClef: Optional[str]  # (None -> G) known values: 'F', 'PERC',
#     VBox: "VBox"
#     Measure: list["Measure"]  # Order is important!!
#
#
# @define
# class VBox:
#     Text: list["Text"]
#
#     @define
#     class Text:
#         style: str  # known values: "Title", "Composer"
#         text: str  # the text
#
#
# @define
# class Measure:
#     # as keys?
#     number: int  # v2, not v3
#     len: Optional[str]  # v3 # known values: "3/4", "7/4" (actual time signature)
#
#     # children
#     voice: list["voice"]  # v3, not v2
#
#     # skipping chords
#     Tempo: "Tempo"  # v1.14
#     Dynamic: "Dynamic"  # v1.14
#     TimeSig: "TimeSig"  # v1.14
#     KeySig: "KeySig"  # v1.14
#
#     @define
#     class Tempo:
#         tempo: float
#         style: int
#         subtype: str  # known values: "Tempo"
#         systemFlag: int  # known values: 1
#         html_data: bs4.element.Tag  # important! text is here  e.g. "Larghetto"
#
#         @property
#         def html_text(self) -> str:
#             return self.html_data.text
#
#     @define
#     class Dynamic:
#         style: int  # known values: 12
#         subtype: str  # known values: "p"
#
#     @define
#     class TimeSig:
#         subtype: int  # known values: 388, 1073750148
#         tick: Optional[int]  # known values: 80640
#         den: int  # known values: 4, 4
#         nom1: int  # known values: 2, 6
#         nom2: Optional[int]  # known values: 2
#
#     @define
#     class KeySig:
#         subtype: int
#         KeySym: "KeySym"
#         showCourtesySig: bool  # known values: 1
#         showNaturals: bool  # known values: 1
#
#         @define
#         class KeySym:
#             sym: int
#             pos_x: str  # known values: 0, 0.5, 1, 2, 2.5, 3
#             pos_y: str  # same as x
#
#
# @define
# class voice:
#     Tempo: list["Tempo"]
#     elements: list[
#         Union["Rest", "Chord", "Tuplet", "Harmony", "Dynamic", "Symbol"]
#     ]  # Order matters!!
#     Clef: "Clef"  # v3
#     KeySig: "KeySig"
#     TimeSig: "TimeSig"
#
#     @define
#     class Clef:
#         concertClefType: str  # known values: G
#         transposingClefType: str  # known values: G
#
#     @define
#     class Symbol:
#         name: str  # known values: "pedalasterisk" (v1)
#
#     @define
#     class KeySig:
#         accidental: int  # v3 # known values: 1
#
#
# @define
# class TimeSig:
#     sigN: str  # v2, v3 # known values: 4
#     sigD: str  # v2, v3 # known values: 4
#     showCourtesySig: bool  # v2 # known values: 1
#
#
# @define
# class Dynamic:
#     # apply to the next Chord, unless tick is specified (compare ticks to see which is applied?)
#     style: int  # font size?
#     subtype: str  # known values: "pp", "p"
#     tick: int
#
#
# @define
# class Tuplet:
#     # apply to the next Chords and Rests
#     id: str
#     tick: int
#     numberType: int  # known values: 0
#     bracketType: int  # known values: 0
#     normalNotes: int  # known values: 6 !important
#     actualNotes: int  # known values: 11 !important
#     baseNote: str  # known values: "eight", ... !important
#     Number: "Number"
#
#     @define
#     class Number:
#         style: int  # known values: 21
#         subtype: str  # known values: "Tuplet"
#
#
# @define
# class Tempo:
#     tempo: float  # 81 -> 1.35  # 80 -> 1.33333
#     followText: bool  # known values: "1", "0"
#     text: str  # e.g. <sym>metNoteQuarterUp</sym> = 80
#
#
# @define
# class Harmony:
#     # Latches onto the next Rest/Chord
#     # E7/A -> root,name,base = 18,7,17
#     root: int  # known values: 13-F,14-C, 15-G, 16-D, 17-A, 18-E, 19-B
#     name: str  # known values: "m", "7"
#     base: int  # known values: same as root
#     play: bool  # known values: "0"
#
#
# @define
# class Rest:
#     durationType: str  # known values: "whole", "half", "quarter", "eight", "16th", "32nd", "64th", "128th"
#     dots: Optional[int]
#
#
# @define
# class Chord:
#     track: int  # v2.06 # known values: "1" = voice 2
#     durationType: str  # known values: "whole", "half", "quarter", "eight", "16th", "32nd", "64th", "128th"
#     dots: Optional[int]
#     # Lyrics: Lyrics text
#     Note: list["Note"]
#     tick: Optional[int]
#     appoggiatura: bool  # if exists, true and is not a whole note
#     Articulation: "Articulation"
#     Arpeggio: "Arpeggio"
#
#     @define
#     class Articulation:
#         subtype: str  # known values: "staccato", "sforzato"
#
#     @define
#     class Arpeggio:
#         track: int  # v1.14 #
#         userLen1: float  # v1.14 #
#
#
# @define
# class Note:
#     pitch: int  # MIDI note number https://en.wikipedia.org/wiki/Scientific_pitch_notation#Table_of_note_frequencies
#     tpc: int
#     Accidental: "Accidental"
#     # Spanner > slur / tie > Tie, [next > location > fractions e.g. 1/8]
#
#
# @define
# class Accidental:
#     subtype: str  # known value: "accidentalNatural" (v3), "accidentalSharp" (v3), "sharp" (1.14), "accidentalDoubleFlat", "accidentalDoubleSharp"
#     track: Optional[int]  # v1.14
