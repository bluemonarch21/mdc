from typing import Optional, ClassVar, Union

import bs4.element
from attr import define


@define
class MuseScore:
    # attributes
    version: str

    # child elements
    programVersion: str
    programRevision: str
    siglist: list["sig"]  # v1.14 only
    tempolist: list["tempo"]  # v1.14 only
    parts: list["Part"]  # v1.14 only
    staffs: list["Staff"]  # v1.14 only

    # class variables
    known_versions: ClassVar[list[str]] = ["1.14"]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "MuseScore":
        if tag is None:
            raise TypeError("Expected bs4.element.Tag, got None")

        version = tag.get("version")
        if version not in cls.known_versions:
            raise ValueError(f"found unknown version: {version}")
        programVersion = tag.find("programVersion", recursive=False).text
        programRevision = tag.find("programRevision", recursive=False).text

        siglist = list(map(sig.from_tag, tag.find("siglist", recursive=False).find_all("sig", recursive=False)))
        tempolist = list(map(tempo.from_tag, tag.find("tempolist", recursive=False).find_all("tempo", recursive=False)))
        parts = list(map(Part.from_tag, tag.find_all("Part", recursive=False)))
        staffs = list(map(Staff.from_tag, tag.find_all("Staff", recursive=False)))

        return cls(
            version=version,
            programVersion=programVersion,
            programRevision=programRevision,
            siglist=siglist,
            tempolist=tempolist,
            parts=parts,
            staffs=staffs,
        )


@define
class sig:
    # attributes
    tick: int

    # child elements
    nom: int
    denom: int
    nom2: Optional[int]
    denom2: Optional[int]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "sig":
        assert tag.name == "sig"
        tick = int(tag.get("tick"))
        nom = int(tag.find("nom", recursive=False).text)
        denom = int(tag.find("denom", recursive=False).text)
        nom2_tag = tag.find("nom2", recursive=False)
        nom2 = None if nom2_tag is None else int(nom2_tag.text)
        denom2_tag = tag.find("denom2", recursive=False)
        denom2 = None if denom2_tag is None else int(denom2_tag.text)
        return cls(tick=tick, nom=nom, nom2=nom2, denom=denom, denom2=denom2)


@define
class tempo:
    # attributes
    tick: int
    text: float

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "tempo":
        assert tag.name == "tempo"
        tick = int(tag.get("tick"))
        text = float(tag.text)  # TODO: handle reversing rounding?
        return cls(tick=tick, text=text)


@define
class Part:
    # child elements
    staffs: list["Part.Staff"]
    name: Optional[str]
    instrument: "Instrument"

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Part":
        assert tag.name == "Part"
        staffs = list(map(Part.Staff.from_tag, tag.find_all("Staff", recursive=False)))
        name_tag = tag.find("name", recursive=False)
        name = None if name_tag is None else name_tag.find("html-data", recursive=False).text
        instrument = Instrument.from_tag(tag.find("Instrument", recursive=False))
        return cls(staffs=staffs, name=name, instrument=instrument)

    @define
    class Staff:
        cleflist: list["clef"]
        keylist: list["key"]

        @classmethod
        def from_tag(cls, tag: bs4.element.Tag) -> "Staff":
            assert tag.name == "Staff"
            cleflist = list(map(clef.from_tag, tag.find("cleflist", recursive=False).find_all("clef", recursive=False)))
            keylist = list(map(key.from_tag, tag.find("keylist", recursive=False).find_all("key", recursive=False)))
            return cls(cleflist=cleflist, keylist=keylist)


@define
class clef:
    tick: int
    idx: int

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "clef":
        assert tag.name == "clef"
        tick = int(tag.get("tick"))
        idx = int(tag.get("idx"))
        return cls(tick=tick, idx=idx)


@define
class key:
    tick: int
    idx: int

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "key":
        assert tag.name == "key"
        tick = int(tag.get("tick"))
        idx = int(tag.get("idx"))
        return cls(tick=tick, idx=idx)


@define
class Instrument:
    trackName: Optional[str]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Instrument":
        assert tag.name == "Instrument"
        trackName_tag = tag.find("trackName", recursive=False)
        trackName = None if trackName_tag is None else trackName_tag.text
        return cls(trackName=trackName)


@define
class Staff:
    # attributes
    id: int

    # child elements
    measures: list["Measure"]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Staff":
        assert tag.name == "Staff"
        id_ = int(tag.get("id"))
        measures = list(map(Measure.from_tag, tag.find_all("Measure", recursive=False)))
        return cls(id=id_, measures=measures)


@define
class Measure:
    # attributes
    number: int  # v1, v2, not v3
    len: Optional[str]  # v3 # known values: "3/4"

    # child elements
    keySig: "KeySig"
    timeSig: "TimeSig"
    children: list[
        Union["Rest", "Chord", "Tuplet", "Harmony", "Dynamic", "Tempo", "Clef"]
    ]  # Order matters!!

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Measure":
        assert tag.name == "Measure"
        number = tag.get("number")
        len_ = tag.get("len")

        KeySig_tag = tag.find("KeySig", recursive=False)
        keySig = None if KeySig_tag is None else KeySig.from_tag(KeySig_tag)
        TimeSig_tag = tag.find("TimeSig", recursive=False)
        timeSig = None if TimeSig_tag is None else TimeSig.from_tag(TimeSig_tag)

        children = []
        for child in tag.children:
            if not isinstance(child, bs4.element.Tag):
                continue
            if child.name == "Dynamic":
                children.append(Dynamic.from_tag(child))
            elif child.name == "Tempo":
                children.append(Tempo.from_tag(child))
            elif child.name == "Tempo":
                children.append(Tempo.from_tag(child))
            elif child.name == "Chord":
                children.append(Chord.from_tag(child))
            elif child.name == "Clef":
                children.append(Clef.from_tag(child))
            elif child.name in ["Beam", "LayoutBreak", "BarLine"]:
                # TODO: log skipped tag
                continue
            else:
                # TODO: log NEW skipped tag
                continue

        return cls(
            number=number, len=len_, keySig=keySig, timeSig=timeSig, children=children
        )


@define
class Tempo:
    tempo: float
    style: int
    subtype: str  # known values: "Tempo"
    text: str  # important! text is here  e.g. "Larghetto"
    # TODO: parse into tempo name + BPM

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Tempo":
        assert tag.name == "Tempo"
        tempo = float(tag.find("tempo", recursive=False).text)
        style = int(tag.find("style", recursive=False).text)
        subtype = tag.find("subtype", recursive=False).text
        assert subtype == "Tempo"
        text = tag.find("html-data", recursive=False).text
        return cls(tempo=tempo, style=style, subtype=subtype, text=text)


@define
class Dynamic:
    # apply to the next Chord, unless tick is specified (compare ticks to see which is applied?)

    style: int  # known values: 12  # font size?
    subtype: Optional[str]  # known values: "pp", "p", "sf"
    tick: Optional[int]
    text: Optional[str]  # e.g. "cresc."

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Dynamic":
        assert tag.name == "Dynamic"
        style = int(tag.find("style", recursive=False).text)
        subtype_tag = tag.find("subtype", recursive=False)
        subtype = None if subtype_tag is None else subtype_tag.text
        tick_tag = tag.find("tick", recursive=False)
        tick = None if tick_tag is None else int(tick_tag.text)
        html_data_tag = tag.find("html-data", recursive=False)
        text = None if html_data_tag is None else html_data_tag.text
        return cls(style=style, subtype=subtype, tick=tick, text=text)


@define
class TimeSig:
    subtype: int  # known values: 388, 1073750148
    tick: Optional[int]  # known values: 80640
    den: int  # known values: 4, 4
    nom1: int  # known values: 2, 6
    nom2: Optional[int]  # known values: 2

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "TimeSig":
        assert tag.name == "TimeSig"
        subtype = int(tag.find("subtype", recursive=False).text)
        tick_tag = tag.find("tick", recursive=False)
        tick = None if tick_tag is None else int(tick_tag.text)
        den = int(tag.find("den", recursive=False).text)
        nom1 = int(tag.find("nom1", recursive=False).text)
        nom2_tag = tag.find("nom2", recursive=False)
        nom2 = None if nom2_tag is None else int(nom2_tag.text)
        return cls(subtype=subtype, tick=tick, den=den, nom1=nom1, nom2=nom2)


@define
class KeySig:
    subtype: Optional[int]  # known values: 4, 75, 180
    keySyms: "KeySym"
    showCourtesySig: Optional[bool]  # known values: 1
    showNaturals: Optional[bool]  # known values: 1

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "KeySig":
        assert tag.name == "KeySig"
        subtype_tag = tag.find("subtype", recursive=False)
        subtype = None if subtype_tag is None else int(subtype_tag.text)
        keySyms = list(map(KeySym.from_tag, tag.find_all("KeySym", recursive=False)))
        showCourtesySig_tag = tag.find("showCourtesySig", recursive=False)
        showCourtesySig = None if showCourtesySig_tag is None else bool(int(showCourtesySig_tag.text))
        showNaturals_tag = tag.find("showNaturals", recursive=False)
        showNaturals = None if showNaturals_tag is None else bool(int(showNaturals_tag.text))
        return cls(
            subtype=subtype,
            keySyms=keySyms,
            showCourtesySig=showCourtesySig,
            showNaturals=showNaturals,
        )


@define
class KeySym:
    sym: int  # known values: 32, 40
    pos_x: str  # known values: -0.5, 0, 0.5, 1, 1.5, 2, 2.5, 3
    pos_y: str  # known values: 0, 1, 2, 3, 4, 5, 6, 7, 8

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "KeySym":
        assert tag.name == "KeySym"
        sym = int(tag.find("sym").text)
        pos_tag = tag.find("pos")
        pos_x = pos_tag.get("x")
        pos_y = pos_tag.get("y")
        return cls(sym=sym, pos_x=pos_x, pos_y=pos_y)


@define
class Clef:
    subtype: Optional[int]  # known values: 4

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Clef":
        assert tag.name == "Clef"
        subtype_tag = tag.find("subtype", recursive=False)
        subtype = None if subtype_tag is None else subtype_tag.text
        return cls(subtype=subtype)

    @property
    def name(self) -> str:
        # see https://en.wikipedia.org/wiki/Clef
        if self.subtype is None:
            return "Treble"
        if self.subtype == 4:
            return "Bass"  # TODO: verify guess
        return f"Unknown(subtype={self.subtype})"


@define
class Tuplet:
    # Define with an "id" (Chords and Rests usually comes after all definitions in the Measure)
    # attributes
    id: str

    # child elements
    track: Optional[int]  # known values: 1, 2
    tick: Optional[int]
    numberType: int  # known values: 0
    bracketType: int  # known values: 0
    normalNotes: int  # known values: 6 !important
    actualNotes: int  # known values: 11 !important
    baseNote: str  # known values: "eight", ... !important
    number: Optional["Number"]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Tuplet":
        assert tag.name == "Tuplet"
        id_ = int(tag.get("id"))
        track_tag = tag.find("track", recursive=False)
        track = None if track_tag is None else int(track_tag.text)
        tick_tag = tag.find("tick", recursive=False)
        tick = None if tick_tag is None else int(tick_tag.text)
        numberType = int(tag.find("numberType", recursive=False).text)
        bracketType = int(tag.find("bracketType", recursive=False).text)
        normalNotes = int(tag.find("normalNotes", recursive=False).text)
        actualNotes = int(tag.find("actualNotes", recursive=False).text)
        baseNote = tag.find("baseNote", recursive=False).text
        Number_tag = tag.find("Number", recursive=False)
        number = None if Number_tag is None else Number.from_tag(Number_tag)

        return cls(
            id=id_,
            track=track,
            tick=tick,
            numberType=numberType,
            bracketType=bracketType,
            normalNotes=normalNotes,
            actualNotes=actualNotes,
            baseNote=baseNote,
            number=number,
        )


@define
class Number:
    style: int  # known values: 21
    subtype: str  # known values: "Tuplet"
    text: str

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Number":
        assert tag.name == "Number"
        style = int(tag.find("style", recursive=False).text)
        subtype = tag.find("subtype", recursive=False).text
        assert subtype == "Tuplet"
        text = tag.find("html-data", recursive=False).text
        return cls(style=style, subtype=subtype, text=text)


@define
class Harmony:  # TODO: Find sample in v1
    # Latches onto the next Rest/Chord
    # E7/A -> root,name,base = 18,7,17
    root: int  # known values: 13-F,14-C, 15-G, 16-D, 17-A, 18-E, 19-B
    name: str  # known values: "m", "7"
    base: int  # known values: same as root
    play: bool  # known values: "0"


@define
class Rest:
    visible: Optional[bool]
    tick: Optional[int]
    durationType: str  # known values: "whole", "half", "quarter", "eight", "16th", "32nd", "64th", "128th"
    dots: Optional[int]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Rest":
        assert tag.name == "Rest"
        visible_tag = tag.find("visible", recursive=False)
        visible = None if visible_tag is None else bool(int(visible_tag.text))
        tick_tag = tag.find("tick", recursive=False)
        tick = None if tick_tag is None else int(tick_tag.text)
        dots_tag = tag.find("dots", recursive=False)
        dots = None if dots_tag is None else int(dots_tag.text)
        durationType = tag.find("durationType", recursive=False).text
        return cls(visible=visible, tick=tick, durationType=durationType, dots=dots)


@define
class Chord:  # TODO
    track: Optional[int]  # v1 known values: "6" # v2.06 known values: "1" = voice 2
    tick: Optional[int]
    tuplet_id: Optional[int]  # v1 # know values: -> matches Tuplet on the outside's id
    dots: Optional[int]
    durationType: str  # known values: "whole", "half", "quarter", "eight", "16th", "32nd", "64th", "128th"
    # lyrics: Optional[str]
    slur: Optional["Slur"]
    appoggiatura: bool  # if exists, true and is not a whole note
    notes: list["Note"]
    articulation: Optional["Articulation"]
    arpeggio: Optional["Arpeggio"]
    # beam: Optional["Beam"]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Chord":
        assert tag.name == "Chord"
        track_tag = tag.find("track", recursive=False)
        track = None if track_tag is None else int(track_tag.text)
        tick_tag = tag.find("tick", recursive=False)
        tick = None if tick_tag is None else int(tick_tag.text)
        Tuplet_tag = tag.find("Tuplet", recursive=False)
        tuplet_id = None if Tuplet_tag is None else int(Tuplet_tag.text)
        dots_tag = tag.find("dots", recursive=False)
        dots = None if dots_tag is None else int(dots_tag.text)
        durationType = tag.find("durationType", recursive=False).text

        Slur_tag = tag.find("Slur", recursive=False)
        slur = None if Slur_tag is None else Slur.from_tag(Slur_tag)
        appoggiatura = tag.find("appoggiatura", recursive=False) is not None

        notes = list(map(Note.from_tag, tag.find_all("Note", recursive=False)))

        Articulation_tag = tag.find("Articulation", recursive=False)
        articulation = (
            None
            if Articulation_tag is None
            else Articulation.from_tag(Articulation_tag)
        )
        Arpeggio_tag = tag.find("Arpeggio", recursive=False)
        arpeggio = None if Arpeggio_tag is None else Arpeggio.from_tag(Arpeggio_tag)

        return cls(
            track=track,
            tick=tick,
            tuplet_id=tuplet_id,
            dots=dots,
            durationType=durationType,
            slur=slur,
            appoggiatura=appoggiatura,
            notes=notes,
            articulation=articulation,
            arpeggio=arpeggio,
        )


@define
class Articulation:
    subtype: Optional[str]  # known values: "staccato", "sforzato"
    track: Optional[int]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Articulation":
        assert tag.name == "Articulation"
        subtype_tag = tag.find("subtype", recursive=False)
        subtype = None if subtype_tag is None else subtype_tag.text
        track_tag = tag.find("track", recursive=False)
        track = None if track_tag is None else int(track_tag.text)
        return cls(subtype=subtype, track=track)


@define
class Arpeggio:
    track: Optional[int]
    userLen1: Optional[float]
    # v3: subtype 0

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Arpeggio":
        assert tag.name == "Arpeggio"
        track_tag = tag.find("track", recursive=False)
        track = None if track_tag is None else int(track_tag.text)
        userLen1_tag = tag.find("userLen1", recursive=False)
        userLen1 = None if userLen1_tag is None else float(userLen1_tag.text)
        return cls(track=track, userLen1=userLen1)


@define
class Slur:
    type: str  # known values: "start", "stop"
    number: int  # seems to be id linked with Slur definition elsewhere

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Slur":
        assert tag.name == "Slur"
        type_ = tag.get("type")
        number = int(tag.get("number"))
        return cls(type=type_, number=number)


@define
class Note:
    track: Optional[int]
    visible: Optional[bool]
    pitch: int  # MIDI note number https://en.wikipedia.org/wiki/Scientific_pitch_notation#Table_of_note_frequencies
    tpc: int
    tie: bool
    accidental: Optional["Accidental"]
    symbol: Optional["Symbol"]
    veloType: Optional[str]  # known values: "user"
    velocity: Optional[int]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Note":
        assert tag.name == "Note"
        track_tag = tag.find("track", recursive=False)
        track = None if track_tag is None else int(track_tag.text)
        visible_tag = tag.find("visible", recursive=False)
        visible = None if visible_tag is None else bool(int(visible_tag.text))

        pitch = int(tag.find("pitch", recursive=False).text)
        tpc = int(tag.find("tpc", recursive=False).text)
        tie = tag.find("Tie", recursive=False) is not None

        Accidental_tag = tag.find("Accidental", recursive=False)
        accidental = (
            None if Accidental_tag is None else Accidental.from_tag(Accidental_tag)
        )
        Symbol_tag = tag.find("Symbol", recursive=False)
        symbol = None if Symbol_tag is None else Symbol.from_tag(Symbol_tag)
        veloType_tag = tag.find("veloType", recursive=False)
        veloType = None if veloType_tag is None else veloType_tag.text
        velocity_tag = tag.find("velocity", recursive=False)
        velocity = None if velocity_tag is None else int(velocity_tag.text)
        return cls(
            track=track,
            visible=visible,
            pitch=pitch,
            tpc=tpc,
            tie=tie,
            accidental=accidental,
            symbol=symbol,
            veloType=veloType,
            velocity=velocity,
        )


@define
class Symbol:
    name: str  # known values: "pedalasterisk" (v1) "pedal ped"

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Symbol":
        assert tag.name == "Symbol"
        name = tag.find("name", recursive=False).text
        return cls(name=name)


@define
class Accidental:
    subtype: str  # known value: "accidentalNatural" (v3), "accidentalSharp" (v3), "sharp" (1.14), "accidentalDoubleFlat", "accidentalDoubleSharp"
    track: Optional[int]
    visible: Optional[bool]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Accidental":
        assert tag.name == "Accidental"
        subtype = tag.find("subtype", recursive=False).text
        track_tag = tag.find("track", recursive=False)
        track = None if track_tag is None else int(track_tag.text)
        visible_tag = tag.find("visible", recursive=False)
        visible = None if visible_tag is None else bool(int(visible_tag.text))
        return cls(subtype=subtype, track=track, visible=visible)
