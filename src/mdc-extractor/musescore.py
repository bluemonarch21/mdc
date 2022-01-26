from typing import ClassVar, Optional, Union

from attrs import define, field


@define
class MuseScore:
    version: str  # known versions: 1.14, 2.06, 3.01, 3.02
    program_version: str


@define
class Score:
    arranger: str
    composer: str
    creationDate: str
    lyricist: str
    movementNumber: str
    movementTitle: str
    workNumber: str
    workTitle: str
    Part: list["Part"]
    Staff: list["Staff"]

    @property
    def feature_playing_speed(self):
        for part in self.Part:
            for staff in part.Staff:
                for measure in staff.Measure:
                    for v in measure.voice:
                        v.Tempo


@define
class Part:
    Staff: list["Staff"]
    trackName: str
    Instrument: "Instrument"


@define
class Staff:
    id: int
    defaultClef: Optional[str]  # (None -> G) known values: 'F', 'PERC',
    VBox: "VBox"
    Measure: list["Measure"]  # Order is important!!


@define
class VBox:
    Text: list["Text"]


@define
class Text:
    style: str  # known values: "Title", "Composer"
    text: str  # the text


@define
class Measure:
    number: int  # only in some version, e.g. 2 (not in 3
    voice: list["voice"]


@define
class voice:
    Tempo: list["Tempo"]
    elements: list[
        Union["Rest", "Chord", "Tuplet", "Harmony", "Dynamic"]
    ]  # Order matters!!
    # KeySig
    # TimeSig  # TODO: IMPORTANT need to know what makes up 1 measure


@define
class Dynamic:
    # apply to the next Chord, unless tick is specified (compare ticks to see which is applied?)
    style: int  # font size?
    subtype: str  # known values: "pp", "p"
    tick: int


@define
class Tuplet:
    # apply to the next Chords and Rests
    id: str
    tick: int
    numberType: int  # known values: 0
    bracketType: int  # known values: 0
    normalNotes: int  # known values: 6 !important
    actualNotes: int  # known values: 11 !important
    baseNote: str  # known values: "eight", ... !important
    Number: "Number"

    @define
    class Number:
        style: int  # known values: 21
        subtype: str  # known values: "Tuplet"


@define
class Tempo:
    tempo: float  # 81 -> 1.35  # 80 -> 1.33333
    followText: bool  # known values: "1", "0"
    text: str  # e.g. <sym>metNoteQuarterUp</sym> = 80


@define
class Harmony:
    # Latches onto the next Rest/Chord
    # E7/A -> root,name,base = 18,7,17
    root: int  # known values: 13-F,14-C, 15-G, 16-D, 17-A, 18-E, 19-B
    name: str  # known values: "m", "7"
    base: int  # known values: same as root
    play: bool  # known values: "0"


@define
class Rest:
    durationType: str  # known values: "whole", "half", "quarter", "eight", "16th", "32nd", "64th", "128th"
    dots: Optional[int]


@define
class Chord:
    durationType: str  # known values: "whole", "half", "quarter", "eight", "16th", "32nd", "64th", "128th"
    dots: Optional[int]
    # Lyrics: Lyrics text
    Note: list["Note"]
    tick: Optional[int]
    appoggiatura: bool  # if exists, true and is not a whole note
    Articulation: "Articulation"

    @define
    class Articulation:
        subtype: str  # known values: "staccato", "sforzato"


@define
class Note:
    pitch: int  # MIDI note number https://en.wikipedia.org/wiki/Scientific_pitch_notation#Table_of_note_frequencies
    tpc: int
    Accidental: "Accidental"
    # Spanner > slur / tie > Tie, [next > location > fractions e.g. 1/8]


@define
class Accidental:
    subtype: str  # known value: "accidentalNatural" (v3), "accidentalSharp" (v3), "sharp" (1.14), "accidentalDoubleFlat", "accidentalDoubleSharp"


@define
class Instrument:
    longName: str  # long name used to label parts on the 1st page
    shortName: str  # short name used to label parts from 2nd page
    trackName: str  # English name of the track?
    instrumentId: str  # id of the instrument, e.g. keyboard.piano.grand
    Articulation: list["Articulation"]
    # channels: list['Channel']  # MIDI info for channels (?)

    @define
    class Articulation:
        """museScore.Score.Part.Instrument.Articulation"""

        # TODO: record known articulation names (these increase the difficulty of a piece)
        name: str  # e.g. staccato, tenuto, marcato
        velocity: int  # loudness (can go up beyond 100)
        gateTime: int  # 0-100 how long the sound lasts
