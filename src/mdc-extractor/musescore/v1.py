from collections.abc import Iterator
from itertools import chain, cycle
from typing import ClassVar, Optional, Union

import bs4.element
import numpy as np
from attr import define, evolve, field, frozen

from features import Features, displacement_cost
from musescore.common import get_average_pitch_from_iterator, get_features, get_vbox_text, is_piano
from musescore.proto import note_possible_tags
from musescore.utils import get_bpm, get_duration_type, get_pulsation, get_tick_length, tick_length_to_pulsation
from utils.arr import bisect


@define
class MuseScore:
    # attributes
    version: str

    # child elements
    programVersion: str
    programRevision: str
    siglist: "SigList"  # v1 only
    tempolist: list["tempo"]  # v1 only
    parts: list["Part"]
    staffs: list["Staff"]

    # class variables
    known_versions: ClassVar[list[str]] = ["1.14"]

    tempos: list["Tempo"] = field(init=False, factory=list)
    tempo_ticks: list[int] = field(init=False, factory=list)

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "MuseScore":
        if tag is None:
            raise TypeError("Expected bs4.element.Tag, got None")

        version = tag.get("version")
        if version not in cls.known_versions:
            raise ValueError(f"found unknown version: {version}")
        programVersion = tag.find("programVersion", recursive=False).text
        programRevision = tag.find("programRevision", recursive=False).text

        siglist = SigList(
            list(
                map(
                    sig.from_tag,
                    tag.find("siglist", recursive=False).find_all("sig", recursive=False),
                )
            )
        )

        tempolist = list(
            map(
                tempo.from_tag,
                tag.find("tempolist", recursive=False).find_all("tempo", recursive=False),
            )
        )
        parts = list(map(Part.from_tag, tag.find_all("Part", recursive=False)))
        inst = cls(
            version=version,
            programVersion=programVersion,
            programRevision=programRevision,
            siglist=siglist,
            tempolist=tempolist,
            parts=parts,
            staffs=[],
        )
        staffs = list(map(Staff.from_tag, tag.find_all("Staff", recursive=False), cycle([inst])))
        inst.staffs = staffs
        inst.count_tempos()
        return inst

    def get_features(self) -> Features:
        staffs = self.get_piano_staffs()
        if not staffs:
            return None
        return get_features(*staffs)

    def get_piano_staffs(self) -> list["Staff"]:
        output = []
        i = 0
        for part in self.parts:
            if part.is_piano:
                if len(part.staffs) == 2:
                    # assumes staffs are sorted and their ordering corresponds to part.staffs
                    output.extend((self.staffs[i], self.staffs[i + 1]))
                elif len(part.staffs) == 1:
                    # TODO: Log piano has only 1 staff
                    # retval.append(self.staffs[i])
                    pass
                else:
                    # TODO: Log piano has no staffs
                    pass
            i += len(part.staffs)
        if len(output) != 0 and len(output) != 2:
            # TODO: Log score does not have left and right hand piano
            pass
        return output

    def count_tempos(self) -> None:
        tempos: list[Tempo] = []
        for staff in self.staffs:
            tempos_with_no_tick: list[Tempo] = []
            for measure in staff.measures:
                strokes: list[Union[Chord, Rest]] = []
                stroke_ticks: list[int] = []
                for child in measure.children:
                    if isinstance(child, Tempo):
                        tempos.append(child)
                        if child.tick is None:
                            tempos_with_no_tick.append(child)
                        continue
                    if isinstance(child, (Chord, Rest)):
                        strokes.append(child)
                        if child.tick is not None:
                            stroke_ticks.append(child.tick)
                        else:
                            stroke_ticks.append(stroke_ticks[-1] + child.tick_length if stroke_ticks else measure.tick)
                        for t in tempos_with_no_tick:
                            if t.tick is None:
                                t.tick = stroke_ticks[-1]
                        tempos_with_no_tick = []
            assert not tempos_with_no_tick, tempos_with_no_tick
            tempos.sort(key=lambda t: t.tick)
        self.tempos = tempos
        self.tempo_ticks = [t.tick for t in tempos]

    @property
    def meta_info(self) -> dict[str, str]:
        return get_vbox_text(self.staffs)


@frozen
class SigList:
    """Provides access to calculated measure ticks from <siglist>"""

    siglist: list["sig"]
    measure_ticks: list[int] = field(init=False, factory=list)
    measure_tick_lengths: list[int] = field(init=False, factory=list)
    _iterator: Iterator[tuple[int, int]] = field(init=False)

    def __attrs_post_init__(self):
        object.__setattr__(self, "_iterator", self._iterate())

    def _iterate(self) -> Iterator[tuple[int, int]]:
        tick = 0
        i = 0
        while True:
            if tick == self.siglist[i].tick:
                yield tick, self.siglist[i].actual_measure_tick_length
                tick += self.siglist[i].actual_measure_tick_length
                continue
            if (i == len(self.siglist) - 1) or (self.siglist[i].tick < tick < self.siglist[i + 1].tick):
                yield tick, self.siglist[i].nominal_measure_tick_length
                tick += self.siglist[i].nominal_measure_tick_length
                continue
            if tick > self.siglist[i].tick and tick >= self.siglist[i + 1].tick:
                i += 1

    def get_tick(self, measure: int) -> int:
        """Returns the tick for the measure, given index"""
        while measure >= len(self.measure_ticks):
            tick, tick_length = self._iterator.__next__()
            self.measure_ticks.append(tick)
            self.measure_tick_lengths.append(tick_length)
        return self.measure_ticks[measure]

    def get_tick_length(self, measure: int) -> int:
        """Returns the tick length for the measure, given index"""
        while measure >= len(self.measure_tick_lengths):
            tick, tick_length = self._iterator.__next__()
            self.measure_ticks.append(tick)
            self.measure_tick_lengths.append(tick_length)
        return self.measure_tick_lengths[measure]


@define
class sig:
    # attributes
    tick: int

    # child elements
    nom: int  # actual (how many notes in that measure) (e.g. pickup measure)
    denom: int  # actual
    nom2: Optional[int]  # nominal (the time signature) if different from actual
    denom2: Optional[int]  # nominal (the time signature) if different from actual

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

    @property
    def actual_nominator(self) -> int:
        """How many beats in that measure. Different from nominal in case of pickup measures."""
        return self.nom

    @property
    def nominal_nominator(self) -> int:
        """How many beats in a measure"""
        return self.nom if self.nom2 is None else self.nom2

    @property
    def actual_denominator(self) -> int:
        """What note is a single beat. Different from nominal in case of pickup measures."""
        return self.denom

    @property
    def nominal_denominator(self) -> int:
        """What note is a single beat"""
        return self.denom if self.denom2 is None else self.denom2

    @property
    def nominal_measure_tick_length(self) -> int:
        """Nominal tick length of a measure"""
        return get_tick_length(get_duration_type(self.nominal_denominator)) * self.nominal_nominator

    @property
    def actual_measure_tick_length(self) -> int:
        """Actual tick length of the overwritten measure"""
        return get_tick_length(get_duration_type(self.actual_denominator)) * self.actual_nominator


@define
class tempo:
    # attributes
    tick: int  # time but not in seconds
    text: float  # e.g. 1.33333, 1.66667

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
    name: Optional[str]  # v1 only  # known values: "Piano"
    instrument: "Instrument"

    known_piano_values: ClassVar[list[str]] = [
        "piano",
        "grand piano",
        "keyboard",
        "pno.",
    ]
    known_not_piano_values: ClassVar[list[str]] = []

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Part":
        assert tag.name == "Part"
        staffs = list(map(Part.Staff.from_tag, tag.find_all("Staff", recursive=False)))
        name_tag = tag.find("name", recursive=False)
        name = (
            None if name_tag is None else name_tag.find("html-data", recursive=False).find("body").get_text(strip=True)
        )
        instrument = Instrument.from_tag(tag.find("Instrument", recursive=False))
        return cls(staffs=staffs, name=name, instrument=instrument)

    @property
    def is_piano(self) -> bool:
        return is_piano(self)

    @define
    class Staff:
        cleflist: list["clef"]  # v1 only
        keylist: list["key"]  # v1 only

        @classmethod
        def from_tag(cls, tag: bs4.element.Tag) -> "Staff":
            assert tag.name == "Staff"
            cleflist = list(
                map(
                    clef.from_tag,
                    tag.find("cleflist", recursive=False).find_all("clef", recursive=False),
                )
            )
            keylist = list(
                map(
                    key.from_tag,
                    tag.find("keylist", recursive=False).find_all("key", recursive=False),
                )
            )
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
    parent: "MuseScore"

    # attributes
    id: int  # starts at 1

    # child elements
    vbox: Optional["VBox"]
    measures: list["Measure"]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag, parent: "MuseScore") -> "Staff":
        assert tag.name == "Staff"
        id_ = int(tag.get("id"))
        vbox_tag = tag.find("VBox", recursive=False)
        vbox = None if vbox_tag is None else VBox.from_tag(vbox_tag)
        inst = cls(parent=parent, id=id_, vbox=vbox, measures=[])
        list(
            map(
                Measure.from_tag,
                tag.find_all("Measure", recursive=False),
                cycle([inst]),
            )
        )
        return inst

    @property
    def chords(self) -> Iterator["Chord"]:
        for measure in self.measures:
            for stroke in measure.strokes:
                if isinstance(stroke, Chord):
                    yield stroke

    @property
    def notes(self) -> Iterator["Note"]:
        for measure in self.measures:
            for child in measure.children:
                if isinstance(child, Chord):
                    for note in child.notes:
                        yield note

    def get_average_pitch(self) -> Optional[float]:
        return get_average_pitch_from_iterator(self.notes)

    def get_hand_displacement_rate(self) -> float:
        chords = list(self.chords)
        arr = np.empty(len(chords) - 1, int)
        for i in range(len(chords) - 1):
            arr[i] = displacement_cost(chords[i], chords[i + 1])
        return arr.mean() / 2

    def get_polyphony_rate(self) -> float:
        num_chord_strokes = 0
        num_strokes = 0
        for measure in self.measures:
            for stroke in measure.strokes:
                if isinstance(stroke, Chord):
                    if not all(n.tie for n in stroke.notes):
                        # count as new stroke if at least one note is not tied
                        # if all is tied, it just is the old stroke with longer tick length
                        num_chord_strokes += int(stroke.is_chord)
                        num_strokes += 1
        return num_chord_strokes / num_strokes

    def get_playing_speed(self) -> float:
        if not self.parent.tempos:
            return None
        tempo_chords: list[list[Chord]] = [[] for _ in range(len(self.parent.tempos))]
        last_tick: int
        for measure in self.measures:
            for stroke in measure.strokes:
                if isinstance(stroke, Chord):
                    tempo_idx = bisect(self.parent.tempo_ticks, measure.get_stroke_tick(stroke))[1] - 1
                    tempo_chords[tempo_idx].append(stroke)
            last_tick = measure.get_last_tick()

        total_area = 0
        playing_speeds = []
        for i in range(len(tempo_chords)):
            tempo = self.parent.tempos[i]
            chords = tempo_chords[i]
            # calculate PS
            if chords:
                ps = sum(c.pulsation for c in chords) / tempo.tempo / len(chords)
            else:
                ps = 0
            playing_speeds.append(ps)
            # calculate average PS
            if i == len(self.parent.tempos) - 1:  # last element
                # maybe do: handle no strokes?
                del_x = last_tick - tempo.tick
            else:
                del_x = self.parent.tempos[i + 1].tick - tempo.tick
            y = ps
            total_area += del_x * y
        avg_ps = total_area / last_tick

        # TODO: numpy calculate variance PS
        return avg_ps


@define
class VBox:
    texts: list["VBox.Text"]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "VBox":
        assert tag.name == "VBox"
        texts = list(map(cls.Text.from_tag, tag.find_all("Text", recursive=False)))
        return cls(texts=texts)

    @define
    class Text:
        subtype: str  # known values: "Title", "Subtitle", "Composer",
        text: str

        @classmethod
        def from_tag(cls, tag: bs4.element.Tag) -> "VBox.Text":
            assert tag.name == "Text"
            subtype = tag.find("subtype", recursive=False).text
            text = tag.find("html-data", recursive=False).find("body").get_text(strip=True)
            return cls(subtype=subtype, text=text)


@define
class Measure:
    parent: "Staff"

    # attributes
    number: int  # v1, v2, not v3  # may just be the display measure number (some are excluded from counting)
    len: Optional[str]  # v3 # known values: "3/4"

    # child elements
    keySig: "KeySig"
    timeSig: "TimeSig"
    children: list[Union["Rest", "Chord", "Tuplet", "Harmony", "Dynamic", "Tempo", "Clef"]]  # Order matters!!

    idx: int = field(init=False)
    _strokes: Optional[list[Union["Chord", "Rest"]]] = field(init=False, default=None)
    _stroke_ticks: Optional[list[int]] = field(init=False, default=None)

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag, parent: "Staff") -> "Measure":
        assert tag.name == "Measure"
        number = int(tag.get("number"))
        len_ = tag.get("len")

        key_sig_tag = tag.find("KeySig", recursive=False)
        keySig = None if key_sig_tag is None else KeySig.from_tag(key_sig_tag)
        time_sig_tag = tag.find("TimeSig", recursive=False)
        timeSig = None if time_sig_tag is None else TimeSig.from_tag(time_sig_tag)

        idx = parent.measures.__len__()
        # assert number == idx + 1, f"{number=} {idx=} {parent.id=} {parent.measures[-1].children=}"
        inst = cls(
            parent=parent,
            number=number,
            len=len_,
            keySig=keySig,
            timeSig=timeSig,
            children=[],
        )
        inst.idx = idx
        parent.measures.append(inst)

        for child in tag.children:
            if not isinstance(child, bs4.element.Tag):
                continue
            if child.name == "Dynamic":
                inst.children.append(Dynamic.from_tag(child))
            elif child.name == "Tempo":
                inst.children.append(Tempo.from_tag(child))
            elif child.name == "Rest":
                inst.children.append(Rest.from_tag(child, inst))
            elif child.name == "Chord":
                inst.children.append(Chord.from_tag(child))
            elif child.name == "Clef":
                inst.children.append(Clef.from_tag(child))
            elif child.name == "Harmony":
                inst.children.append(Harmony.from_tag(child))
            elif child.name in ["Beam", "LayoutBreak", "BarLine"]:
                # TODO: log skipped tag
                continue
            else:
                # TODO: log NEW skipped tag
                continue

    @property
    def previous(self) -> Optional["Measure"]:
        return None if self.idx == 0 else self.parent.measures[self.idx - 1]

    @property
    def tick(self) -> int:
        return self.parent.parent.siglist.get_tick(measure=self.idx)
        # if self.idx == 0:
        #     return 0
        # return self.previous.tick + self.previous.tick_length

    @property
    def tick_length(self) -> int:
        # just ask MuseScore class
        return self.parent.parent.siglist.get_tick_length(measure=self.idx)
        # for v2, v3
        # for child in self.children:
        #     if isinstance(child, TimeSig):
        #         return child.measure_tick_length
        # return self.previous.tick_length

    def _compute_strokes(self) -> None:
        strokes: list[Union[Chord, Rest]] = []
        stroke_ticks: list[int] = []
        for child in self.children:
            if isinstance(child, (Chord, Rest)):
                if child.tick is not None:
                    stroke_tick = child.tick
                else:
                    stroke_tick = stroke_ticks[-1] + child.tick_length if stroke_ticks else self.tick
                # TODO: Handle differently in v2, v3
                if stroke_tick in stroke_ticks:  # old stroke, new voice
                    idx = stroke_ticks.index(stroke_tick)
                    old_stroke = strokes[idx]
                    if isinstance(old_stroke, Rest):
                        # actually should depend on what the next stroke is
                        if child.tick_length < old_stroke.tick_length:
                            # presumably something would come right after
                            strokes[idx] = child
                    elif isinstance(old_stroke, Chord):
                        if isinstance(child, Chord):
                            # merge chords, ignore Rest
                            # actually should depend on what the next stroke is
                            if child.tick_length < old_stroke.tick_length:
                                # presumably something would come right after
                                new_pitches = [n.pitch for n in child.notes]
                                notes = list(
                                    chain(child.notes, (n for n in old_stroke.notes if n.pitch not in new_pitches))
                                )
                                strokes[idx] = evolve(child, notes=notes)
                            else:
                                old_pitches = [n.pitch for n in old_stroke.notes]
                                notes = list(
                                    chain(old_stroke.notes, (n for n in child.notes if n.pitch not in old_pitches))
                                )
                                strokes[idx] = evolve(old_stroke, notes=notes)
                    else:
                        raise AssertionError("Stroke should be Rest or Chord")
                else:  # new stroke
                    strokes.append(child)
                    stroke_ticks.append(stroke_tick)
        self._strokes = strokes
        self._stroke_ticks = stroke_ticks

    @property
    def strokes(self) -> list[Union["Chord", "Rest"]]:
        """Returns each distinct stroke, merging all voices."""
        if self._strokes is None:
            self._compute_strokes()
        return list(self._strokes)

    @property
    def stroke_ticks(self) -> set[int]:
        """Returns ticks for each distinct stroke, merging all voices."""
        if self._stroke_ticks is None:
            self._compute_strokes()
        # TODO: Use np.unique() instead
        result = set(self._stroke_ticks)
        assert len(result) == len(self._stroke_ticks)
        return result

    def get_stroke_tick(self, stroke: Union["Chord", "Rest"]) -> int:
        """Returns the tick of the given stroke."""
        if self._stroke_ticks is None:
            self._compute_strokes()
        return self._stroke_ticks[self.strokes.index(stroke)]

    def get_last_tick(self) -> int:
        """Returns the last tick in this measure."""
        if self._stroke_ticks is None:
            self._compute_strokes()
        return self._stroke_ticks[-1]


@define
class KeySig:  # v1 version
    subtype: Optional[int]  # v1 only  # known values: 4, 75, 180
    keySyms: "KeySym"  # v1 only
    showCourtesySig: Optional[bool]  # v1 only  # known values: 1
    showNaturals: Optional[bool]  # v1 only  # known values: 1

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

    @property
    def denominator_duration_type(self) -> str:
        """Specifies the durationType of a single beat"""
        return get_duration_type(self.den)

    @property
    def nominator(self) -> int:
        """Number of beats in one measure"""
        if self.nom2 is not None and self.nom2 != self.nom1:
            print(self)
            # TODO: log
        return self.nom2 if self.nom2 is not None else self.nom1

    @property
    def measure_tick_length(self) -> int:
        """Tick length of a measure under this time signature"""
        return get_tick_length(self.denominator_duration_type) * self.nominator


@define
class Tempo:
    tempo: float
    style: int
    subtype: str  # known values: "Tempo"
    _tick: Optional[int]
    text: str  # important! text is here  e.g. "Larghetto" # TODO: parse into tempo name + BPM
    _cal_tick: Optional[int] = field(init=False, default=None)

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Tempo":
        assert tag.name == "Tempo"
        tempo = float(tag.find("tempo", recursive=False).text)
        style = int(tag.find("style", recursive=False).text)
        subtype = tag.find("subtype", recursive=False).text
        assert subtype == "Tempo"
        tick_tag = tag.find("tick", recursive=False)
        _tick = None if tick_tag is None else int(tick_tag.text)
        # <sym>unicodeNoteQuarterUp</sym>
        text = tag.find("html-data", recursive=False).find("body").get_text(strip=True)
        return cls(tempo=tempo, style=style, subtype=subtype, tick=_tick, text=text)

    @property
    def bpm(self) -> float:
        """Beats Per Minute"""
        return get_bpm(self.tempo)

    @property
    def tick(self) -> Optional[int]:
        return self._tick or self._cal_tick

    @tick.setter
    def tick(self, value: int):
        self._cal_tick = value


@define
class Dynamic:
    # apply to the next Chord, unless tick is specified (compare ticks to see which is applied?)

    style: int  # known values: 12  # font size?
    subtype: Optional[str]  # known values: "pp", "p", "sf"
    tick: Optional[int]
    # TODO: remove text in <style>
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
        text = None if html_data_tag is None else html_data_tag.find("body").get_text(strip=True)
        return cls(style=style, subtype=subtype, tick=tick, text=text)


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
class Tuplet:  # TODO: consider tuplets
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
        number_tag = tag.find("Number", recursive=False)
        number = None if number_tag is None else Number.from_tag(number_tag)

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
        text = tag.find("html-data", recursive=False).find("body").get_text(strip=True)
        return cls(style=style, subtype=subtype, text=text)


@define
class Harmony:  # sample: 666
    root: int  # known values: 13-F,14-C, 15-G, 16-D, 17-A, 18-E, 19-B
    extension: str  # known values: 1- major, 16- minor,
    tick: Optional[int]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Harmony":
        assert tag.name == "Harmony"
        root = int(tag.find("root", recursive=False).text)
        extension = int(tag.find("extension", recursive=False).text)
        tick_tag = tag.find("tick", recursive=False)
        tick = None if tick_tag is None else int(tick_tag.text)
        return cls(root, extension, tick)


@define
class Rest:
    parent: "Measure"

    visible: Optional[bool]
    tick: Optional[int]
    durationType: str  # known values: "measure", "whole", "half", "quarter", "eight", "16th", "32nd", "64th", "128th"
    dots: int
    articulation: Optional["Articulation"]  # fermata

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag, parent: "Measure") -> "Rest":
        assert tag.name == "Rest"
        visible_tag = tag.find("visible", recursive=False)
        visible = None if visible_tag is None else bool(int(visible_tag.text))
        tick_tag = tag.find("tick", recursive=False)
        tick = None if tick_tag is None else int(tick_tag.text)
        dots_tag = tag.find("dots", recursive=False)
        dots = 0 if dots_tag is None else int(dots_tag.text)
        durationType = tag.find("durationType", recursive=False).text
        articulation_tag = tag.find("Articulation")
        articulation = None if articulation_tag is None else Articulation.from_tag(articulation_tag)
        return cls(
            parent=parent,
            visible=visible,
            tick=tick,
            durationType=durationType,
            dots=dots,
            articulation=articulation,
        )

    @property
    def pulsation(self) -> float:
        if self.durationType == "measure":
            return tick_length_to_pulsation(self.parent.tick_length)
        return get_pulsation(self.durationType, self.dots)

    @property
    def tick_length(self) -> int:
        if self.durationType == "measure":
            return self.parent.tick_length
        return get_tick_length(self.durationType, self.dots)


@define
class Chord:  # TODO
    track: Optional[int]  # v1 known values: "6" # v2.06 known values: "1" = voice 2
    tick: Optional[int]
    tuplet_id: Optional[int]  # v1 # know values: -> matches Tuplet on the outside's id
    dots: int
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
        tuplet_tag = tag.find("Tuplet", recursive=False)
        tuplet_id = None if tuplet_tag is None else int(tuplet_tag.text)
        dots_tag = tag.find("dots", recursive=False)
        dots = 0 if dots_tag is None else int(dots_tag.text)
        durationType = tag.find("durationType", recursive=False).text

        slur_tag = tag.find("Slur", recursive=False)
        slur = None if slur_tag is None else Slur.from_tag(slur_tag)
        appoggiatura = tag.find("appoggiatura", recursive=False) is not None

        notes = list(map(Note.from_tag, tag.find_all("Note", recursive=False)))

        articulation_tag = tag.find("Articulation", recursive=False)
        articulation = None if articulation_tag is None else Articulation.from_tag(articulation_tag)
        arpeggio_tag = tag.find("Arpeggio", recursive=False)
        arpeggio = None if arpeggio_tag is None else Arpeggio.from_tag(arpeggio_tag)

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

    @property
    def pulsation(self) -> float:
        return get_pulsation(self.durationType, self.dots)

    @property
    def tick_length(self) -> int:
        return get_tick_length(self.durationType, self.dots)

    @property
    def is_chord(self) -> bool:
        return len(self.notes) > 1


@define
class Articulation:  # TODO: account for fermata
    subtype: Optional[str]  # known values: "staccato", "sforzato", "fermata"
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

    possible_tags: ClassVar[list[str]] = ["tpc2"]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Note":
        assert tag.name == "Note"
        note_possible_tags(cls, tag)
        track_tag = tag.find("track", recursive=False)
        track = None if track_tag is None else int(track_tag.text)
        visible_tag = tag.find("visible", recursive=False)
        visible = None if visible_tag is None else bool(int(visible_tag.text))

        pitch = int(tag.find("pitch", recursive=False).text)
        tpc = int(tag.find("tpc", recursive=False).text)
        tie = tag.find("Tie", recursive=False) is not None

        accidental_tag = tag.find("Accidental", recursive=False)
        accidental = None if accidental_tag is None else Accidental.from_tag(accidental_tag)
        symbol_tag = tag.find("Symbol", recursive=False)
        symbol = None if symbol_tag is None else Symbol.from_tag(symbol_tag)
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
    subtype: str  # known values: "accidentalNatural" (v3), "accidentalSharp" (v3), "sharp" (1.14), "accidentalDoubleFlat", "accidentalDoubleSharp"
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
