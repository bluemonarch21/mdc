from collections.abc import Iterator
from functools import reduce
from itertools import chain, cycle
from typing import ClassVar, Optional, Union

import bs4.element
import numpy as np
from attr import define, evolve, field

from features import Features
from musescore.common import (get_average_pitch_from_np_array, get_chords_for_each_tempo, get_features,
                              get_hand_displacement_rate_from_list, get_playing_speed, get_polyphony_rate,
                              get_staffs_from_piano_parts_id, get_vbox_text, is_piano)
from musescore.proto import note_possible_tags
from musescore.utils import get_bpm, get_duration_type, get_pulsation, get_tick_length, tick_length_to_pulsation
from utils.dict import append_value


@define
class MuseScore:
    # attributes
    version: str

    # child elements
    programVersion: str
    programRevision: str
    score: "Score"

    # class variables
    known_versions: ClassVar[list[str]] = ["3.01", "3.02"]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "MuseScore":
        if tag is None:
            raise TypeError("Expected bs4.element.Tag, got None")

        version = tag.get("version")
        if version not in cls.known_versions:
            raise ValueError(f"found unknown version: {version}")
        programVersion = tag.find("programVersion", recursive=False).text
        programRevision = tag.find("programRevision", recursive=False).text
        score = Score.from_tag(tag.find("Score", recursive=False))
        return cls(
            version=version,
            programVersion=programVersion,
            programRevision=programRevision,
            score=score,
        )

    def get_features(self) -> Features:
        staffs = self.score.get_piano_staffs()
        if not staffs:
            return None
        return get_features(*staffs)

    @property
    def meta_info(self) -> dict[str, str]:
        dct = get_vbox_text(self.score.staffs)
        # cannot just override because sometimes vbox text is better (actually most of the time)
        for tag in self.score.metaTags:
            if tag.text:
                append_value(dct, tag.name, tag.text)
        return dct


@define
class Score:
    # child elements
    parts: list["Part"]
    staffs: list["Staff"]  # sorted with id
    metaTags: list["metaTag"]

    tempos: list["Tempo"] = field(init=False, factory=list)
    tempo_ticks: list[int] = field(init=False, factory=list)

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Score":
        assert tag.name == "Score"
        parts = list(map(Part.from_tag, tag.find_all("Part", recursive=False)))
        metaTags = list(map(metaTag.from_tag, tag.find_all("metaTag", recursive=False)))
        inst = cls(
            parts=parts,
            staffs=[],
            metaTags=metaTags,
        )
        staffs = sorted(
            map(Staff.from_tag, tag.find_all("Staff", recursive=False), cycle([inst])),
            key=lambda s: getattr(s, "id"),
        )
        inst.staffs = staffs
        inst.count_tempos()
        return inst

    def count_tempos(self) -> None:
        tempos: list[Tempo] = []
        this_tick = None
        for staff in self.staffs:
            tempos_with_no_tick: list[Tempo] = []
            for measure in staff.measures:
                for voice in measure.voices:
                    strokes: list[Union[Chord, Rest]] = []
                    stroke_ticks: list[int] = []
                    for child in voice.children:
                        if isinstance(child, Tick):
                            this_tick = child.value
                        elif isinstance(child, Tempo):
                            tempos.append(child)
                            if this_tick is not None:
                                child.tick = this_tick
                            else:
                                tempos_with_no_tick.append(child)
                        elif isinstance(child, (Chord, Rest)):
                            strokes.append(child)
                            if this_tick is not None:
                                stroke_ticks.append(this_tick)
                                this_tick = None
                            else:
                                stroke_ticks.append(
                                    stroke_ticks[-1] + child.tick_length if stroke_ticks else measure.tick
                                )
                            for t in tempos_with_no_tick:
                                if t.tick is None:
                                    t.tick = stroke_ticks[-1]
                            tempos_with_no_tick = []
            assert not tempos_with_no_tick, tempos_with_no_tick
            tempos.sort(key=lambda t: t.tick)
        self.tempos = tempos
        self.tempo_ticks = [t.tick for t in tempos]

    def get_piano_staffs(self) -> list["Staff"]:
        output = list(get_staffs_from_piano_parts_id(self.parts, self.staffs))
        if len(output) != 0 and len(output) != 2:
            # TODO: Log score does not have left and right hand piano
            pass
        return output


@define
class metaTag:
    name: str
    text: str

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "metaTag":
        assert tag.name == "metaTag"
        name = tag.get("name")
        text = tag.text
        return cls(name=name, text=text)


@define
class Part:
    # child elements
    staffs: list["Part.Staff"]
    trackName: Optional[str]
    instrument: "Instrument"

    known_piano_values: ClassVar[list[str]] = [
        "piano",
        "grand piano",
        "keyboard",
        "pno.",
        "ピアノ",
        "keyboard.piano",
        "keyboard.harpsichord",
    ]
    known_not_piano_values: ClassVar[list[str]] = []

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Part":
        assert tag.name == "Part"
        staffs = list(map(Part.Staff.from_tag, tag.find_all("Staff", recursive=False)))
        trackName = tag.find("trackName", recursive=False).text
        instrument = Instrument.from_tag(tag.find("Instrument", recursive=False))
        return cls(staffs=staffs, trackName=trackName, instrument=instrument)

    @property
    def is_piano(self) -> bool:
        return is_piano(self)

    @define
    class Staff:
        id: int
        defaultClef: Optional[str]  # new in v3 # known values: "F"

        @classmethod
        def from_tag(cls, tag: bs4.element.Tag) -> "Staff":
            assert tag.name == "Staff"
            id_ = int(tag.get("id"))
            defaultClef_tag = tag.find("defaultClef", recursive=False)
            defaultClef = None if defaultClef_tag is None else defaultClef_tag.text
            return cls(id=id_, defaultClef=defaultClef)


@define
class Instrument:
    # child elements
    longName: Optional[str]
    shortName: Optional[str]
    trackName: str
    instrumentId: Optional[str]
    clef: Optional["Instrument.Clef"]  # new in v3
    articulations: list["Instrument.Articulation"]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Instrument":
        assert tag.name == "Instrument"
        longName_tag = tag.find("longName", recursive=False)
        longName = None if longName_tag is None else longName_tag.text
        shortName_tag = tag.find("shortName", recursive=False)
        shortName = None if shortName_tag is None else shortName_tag.text
        trackName = tag.find("trackName", recursive=False).text
        # trackName_tag = tag.find("trackName", recursive=False)
        # trackName = None if trackName_tag is None else trackName_tag.text
        instrumentId_tag = tag.find("instrumentId", recursive=False)
        instrumentId = None if instrumentId_tag is None else instrumentId_tag.text
        clef_tag = tag.find("clef", recursive=False)
        clef = None if clef_tag is None else cls.Clef.from_tag(clef_tag)

        articulations = list(map(cls.Articulation.from_tag, tag.find_all("Articulation", recursive=False)))
        return cls(
            longName=longName,
            shortName=shortName,
            trackName=trackName,
            instrumentId=instrumentId,
            clef=clef,
            articulations=articulations,
        )

    @define
    class Articulation:
        velocity: int
        gateTime: int

        @classmethod
        def from_tag(cls, tag: bs4.element.Tag) -> "Instrument.Articulation":
            assert tag.name == "Articulation"
            velocity = int(tag.find("velocity", recursive=False).text)
            gateTime = int(tag.find("gateTime", recursive=False).text)
            return cls(velocity=velocity, gateTime=gateTime)

    @define
    class Clef:
        staff: int  # known values: 2
        text: str  # known values: "F"

        @classmethod
        def from_tag(cls, tag: bs4.element.Tag) -> "Instrument.Clef":
            assert tag.name == "clef"
            staff = tag.get("staff")
            # None means it's the only staff in the instrument
            staff = 1 if staff is None else int(staff)
            text = tag.text
            return cls(staff=staff, text=text)


@define
class Staff:
    parent: "Score"

    # attributes
    id: int  # starts at 1

    # child elements
    vbox: Optional["VBox"]
    measures: list["Measure"]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag, parent: "Score") -> "Staff":
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
    def strokes(self) -> Iterator[Union["Chord", "Rest"]]:
        for measure in self.measures:
            for stroke in measure.strokes:
                yield stroke

    @property
    def flattened_chords(self) -> Iterator["Chord"]:
        for stroke in self.strokes:
            if isinstance(stroke, Chord):
                yield stroke

    @property
    def notes(self) -> Iterator["Note"]:
        for measure in self.measures:
            for voice in measure.voices:
                for child in voice.children:
                    if isinstance(child, Chord):
                        for note in child.notes:
                            yield note

    def get_average_pitch(self) -> Optional[float]:
        return get_average_pitch_from_np_array(self.notes)

    def get_hand_displacement_rate(self) -> Optional[float]:
        return get_hand_displacement_rate_from_list(self.flattened_chords)

    def get_polyphony_rate(self) -> Optional[float]:
        return get_polyphony_rate(self.flattened_chords)

    def get_playing_speed(self) -> float:
        if not self.parent.tempos:
            return None
        tempo_chords = get_chords_for_each_tempo(self.measures, self.parent.tempo_ticks)
        last_tick = max(self.measures[-1].stroke_ticks)
        return get_playing_speed(zip(self.parent.tempos, tempo_chords), last_tick)


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
        subtype: Optional[str]  # known values: "Title", "Subtitle", "Composer"
        style: Optional[str]  # known values: "Title", "Subtitle"
        text: str

        @classmethod
        def from_tag(cls, tag: bs4.element.Tag) -> "VBox.Text":
            assert tag.name == "Text"
            subtype_tag = tag.find("subtype", recursive=False)
            subtype = None if subtype_tag is None else subtype_tag.text
            style_tag = tag.find("style", recursive=False)
            style = None if style_tag is None else style_tag.text
            html_data = tag.find("html-data", recursive=False)
            html_text = None if html_data is None else html_data.find("body").get_text(strip=True)
            text = html_text if html_text is not None else tag.find("text", recursive=False).text
            return cls(subtype=subtype, style=style, text=text)


@define
class Measure:
    parent: "Staff"

    # attributes
    len: Optional[str]  # new in v3 # known values: "3/4", "1/8"
    # TODO: Make sure v1 and v2 have tick length

    # child elements
    irregular: bool  # True if exists  # means number is not counted
    voices: list["Voice"]
    keySig: "KeySig"  # in <voice>
    timeSig: "TimeSig"  # in <voice>

    idx: int = field(init=False)
    _tick: Optional[int] = field(init=False, default=None)
    _tick_length: Optional[int] = field(init=False, default=None)
    _strokes: Optional[list[Union["Chord", "Rest"]]] = field(init=False, default=None)
    _stroke_ticks: Optional[list[int]] = field(init=False, default=None)

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag, parent: "Staff") -> "Measure":
        assert tag.name == "Measure"
        len_ = tag.get("len")

        irregular = tag.find("irregular", recursive=False) is not None

        keySig_tag = tag.find("KeySig", recursive=True)
        keySig = None if keySig_tag is None else KeySig.from_tag(keySig_tag)
        timeSig_tag = tag.find("TimeSig", recursive=True)
        timeSig = None if timeSig_tag is None else TimeSig.from_tag(timeSig_tag)

        idx = parent.measures.__len__()
        inst = cls(
            parent=parent,
            len=len_,
            irregular=irregular,
            voices=[],
            keySig=keySig,
            timeSig=timeSig,
        )
        inst.idx = idx

        [Voice.from_tag(t, inst) for t in tag.find_all("voice", recursive=False)]
        # should have at least one <voice> with children
        assert len(inst.voices) != 0
        assert any(len(v.children) != 0 for v in inst.voices), tag.find_all("voice", recursive=False)
        # TODO: maybe just keep the Measure as is?
        for voice in inst.voices:
            for child in voice.children:
                if isinstance(child, RepeatMeasure):
                    inst = evolve(inst.previous)
                    inst.idx = idx
        parent.measures.append(inst)
        inst._compute_ticks()

    @property
    def previous(self) -> Optional["Measure"]:
        return None if self.idx == 0 else self.parent.measures[self.idx - 1]

    @property
    def tick(self) -> int:
        if self._tick is None:
            self._compute_ticks()
        return self._tick

    @property
    def tick_length(self) -> int:
        if self._tick_length is None:
            self._compute_ticks()
        if self.len is not None:
            nominator, denominator = map(int, self.len.split("/"))
            return get_tick_length(get_duration_type(denominator)) * nominator
        return self._tick_length

    def _compute_ticks(self) -> None:
        if self.idx == 0:
            tick = 0
        else:
            tick = self.previous.tick + self.previous.tick_length
        if self.timeSig is not None:
            tick_length = self.timeSig.measure_tick_length
        else:
            if self.previous is not None:
                # use nominal tick length
                tick_length = self.previous._tick_length
            else:
                # First but no Time Signature
                # TODO: Use stroke's value instead
                if self.len is not None:
                    _, denominator = map(int, self.len.split("/"))
                    # assume nominal has nominator as full length
                    tick_length = get_tick_length(get_duration_type(denominator)) * denominator
                else:
                    # assume common time
                    tick_length = get_tick_length("quarter") * 4
        self._tick = tick
        self._tick_length = tick_length

    def _compute_strokes(self) -> None:
        all_strokes: list[list[Union[Chord, Rest]]] = []
        all_stroke_ticks: list[list[int]] = []
        for i, voice in enumerate(self.voices):
            strokes: list[Union[Chord, Rest]] = []
            stroke_ticks: list[int] = []
            for child in voice.children:
                if isinstance(child, (Chord, Rest)):
                    stroke_tick = stroke_ticks[-1] + child.tick_length if stroke_ticks else self.tick
                    strokes.append(child)
                    stroke_ticks.append(stroke_tick)
            all_strokes.append(strokes)
            all_stroke_ticks.append(stroke_ticks)
        # merge
        strokes: list[Union[Chord, Rest]] = []
        stroke_ticks: list[int] = []
        assert len(all_stroke_ticks) != 0
        for t in reduce(np.union1d, all_stroke_ticks):
            common_strokes: list[Union[Chord, Rest]] = []
            for i in range(len(self.voices)):
                for j in range(len(all_stroke_ticks[i])):
                    if t == all_stroke_ticks[i][j]:
                        common_strokes.append(all_strokes[i][j])
            stroke_ticks.append(t)
            assert len(common_strokes) != 0
            if len(common_strokes) == 1:
                strokes.append(common_strokes[0])
            elif len(common_strokes) > 1:
                merged_stroke = common_strokes[0]
                for stroke in common_strokes[1:]:
                    if isinstance(merged_stroke, Rest):
                        # actually should depend on what the next stroke is
                        if stroke.tick_length < merged_stroke.tick_length:
                            # presumably something would come right after
                            merged_stroke = stroke
                    elif isinstance(merged_stroke, Chord):
                        if isinstance(stroke, Chord):
                            # merge chords, ignore Rest
                            # actually should depend on what the next stroke is
                            if stroke.tick_length < merged_stroke.tick_length:
                                # presumably something would come right after
                                new_pitches = [n.pitch for n in stroke.notes]
                                notes = list(
                                    chain(stroke.notes, (n for n in merged_stroke.notes if n.pitch not in new_pitches))
                                )
                                merged_stroke = evolve(stroke, notes=notes)
                            else:
                                old_pitches = [n.pitch for n in merged_stroke.notes]
                                notes = list(
                                    chain(merged_stroke.notes, (n for n in stroke.notes if n.pitch not in old_pitches))
                                )
                                merged_stroke = evolve(merged_stroke, notes=notes)
                    else:
                        raise AssertionError("Stroke should be Rest or Chord")
                strokes.append(merged_stroke)

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
class Voice:
    parent: "Measure"

    # keySig: "KeySig"    # Moved to Measure, TODO: maybe move back?
    # timeSig: "TimeSig"  # Moved to Measure
    children: list[
        Union[
            "Rest",
            "Chord",
            "Tuplet",
            "Harmony",
            "Dynamic",
            "Tempo",
            "Clef",
            "StaffText",
            "Tick",
            "RepeatMeasure",
        ]
    ]  # Order matters!!

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag, parent: "Measure"):
        assert tag.name == "voice"

        inst = cls(
            parent=parent,
            children=[],
        )
        parent.voices.append(inst)

        for child in tag.children:
            if not isinstance(child, bs4.element.Tag):
                continue
            if child.name == "tick":
                inst.children.append(Tick.from_tag(child))
            elif child.name == "Dynamic":
                inst.children.append(Dynamic.from_tag(child))
            elif child.name == "Tempo":
                inst.children.append(Tempo.from_tag(child))
            elif child.name == "Rest":
                inst.children.append(Rest.from_tag(child))
            elif child.name == "Chord":
                inst.children.append(Chord.from_tag(child))
            elif child.name == "Clef":
                inst.children.append(Clef.from_tag(child))
            elif child.name == "StaffText":
                inst.children.append(StaffText.from_tag(child))
            elif child.name == "Harmony":
                inst.children.append(Harmony.from_tag(child))
            elif child.name == "RepeatMeasure":
                inst.children.append(RepeatMeasure.from_tag(child))
            elif child.name in ["Beam", "LayoutBreak", "BarLine"]:
                # TODO: log skipped tag
                continue
            else:
                # TODO: log NEW skipped tag
                continue


@define
class RepeatMeasure:  # TODO: Add in v1, v2 (use assert stroke != 0)
    durationType: str
    duration: "Rest.Duration"

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "RepeatMeasure":
        assert tag.name == "RepeatMeasure"
        durationType = tag.find("durationType", recursive=False).text
        duration_tag = tag.find("duration", recursive=False)
        assert durationType != "measure" or duration_tag is not None
        duration = None if duration_tag is None else Rest.Duration.from_tag(duration_tag)
        assert durationType == "measure", tag  # Assumes it replaces previous measures currently
        return cls(durationType=durationType, duration=duration)


@define
class Tick:
    value: int

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Harmony":
        assert tag.name == "Tick"
        raise NotImplementedError(f"{tag}")
        value = int(tag.text)
        return cls(value=value)


@define
class KeySig:
    lid: Optional[int]  # known values: 5, 3021
    accidental: Optional[int]  # known values: 0, 1, 2, -2
    custom: Optional[int]  # known values: 1
    mode: Optional[str]  # known values: "none"

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "KeySig":
        assert tag.name == "KeySig"
        lid_tag = tag.find("lid", recursive=False)
        lid = None if lid_tag is None else int(lid_tag.text)
        accidental_tag = tag.find("accidental", recursive=False)
        accidental = None if accidental_tag is None else int(accidental_tag.text)
        custom_tag = tag.find("custom", recursive=False)
        custom = None if custom_tag is None else int(custom_tag.text)
        mode_tag = tag.find("mode", recursive=False)
        mode = None if mode_tag is None else mode_tag.text
        return cls(
            lid=lid,
            accidental=accidental,
            custom=custom,
            mode=mode,
        )


@define
class TimeSig:
    subtype: Optional[int]  # known values: 1
    # lid: Optional[int]  # known values:
    # tick: Optional[int]  # known values:
    sigN: int  # known values: 4, 3, 2
    sigD: int  # known values: 4, 4, 4
    # showCourtesySig: bool  # known values:

    # TODO: Find Actual / Nominal example?

    possible_tags: ClassVar[list[str]] = ["tick", "showCourtesySig", "lid"]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "TimeSig":
        assert tag.name == "TimeSig"
        note_possible_tags(cls, tag)
        subtype_tag = tag.find("subtype", recursive=False)
        subtype = None if subtype_tag is None else int(subtype_tag.text)
        sigN = int(tag.find("sigN", recursive=False).text)
        sigD = int(tag.find("sigD", recursive=False).text)
        return cls(
            subtype=subtype,
            sigN=sigN,
            sigD=sigD,
        )

    @property
    def denominator_duration_type(self) -> str:
        """Specifies the durationType of a single beat"""
        return get_duration_type(self.sigD)

    @property
    def nominator(self) -> int:
        """Number of beats in one measure"""
        return self.sigN

    @property
    def measure_tick_length(self) -> int:
        """Tick length of a measure under this time signature"""
        return get_tick_length(self.denominator_duration_type) * self.nominator


@define
class Tempo:
    tempo: float
    # _tick: Optional[int]
    text: str  # important! text is here  e.g. "Larghetto" # TODO: parse into tempo name + BPM
    followText: Optional[bool]  # known values: 1
    lid: Optional[int]  # known values: 4
    visible: Optional[bool]  # known values: 0

    _cal_tick: Optional[int] = field(init=False, default=None)

    possible_tags: ClassVar[list[str]] = ["tick"]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Tempo":
        assert tag.name == "Tempo"
        note_possible_tags(cls, tag)
        tempo = float(tag.find("tempo", recursive=False).text)
        # tick_tag = tag.find("tick", recursive=False)
        # _tick = None if tick_tag is None else int(tick_tag.text)
        # <sym>unicodeNoteQuarterUp</sym>
        text = tag.find("text", recursive=False).text
        followText_tag = tag.find("followText")
        followText = None if followText_tag is None else bool(int(followText_tag.text))
        lid_tag = tag.find("lid")
        lid = None if lid_tag is None else int(lid_tag.text)
        visible_tag = tag.find("visible")
        visible = None if visible_tag is None else bool(int(visible_tag.text))
        return cls(tempo=tempo, text=text, followText=followText, lid=lid, visible=visible)

    @property
    def bpm(self) -> float:
        """Beats Per Minute"""
        return get_bpm(self.tempo)

    @property
    def tick(self) -> Optional[int]:
        return self._cal_tick

    @tick.setter
    def tick(self, value: int):
        self._cal_tick = value


@define
class Dynamic:
    # apply to the next Chord, unless tick is specified (compare ticks to see which is applied?)

    style: Optional[int]  # known values: 12  # font size?
    subtype: str  # known values: "pp", "p", "sf", "f"
    velocity: Optional[int]
    track: Optional[int]
    # tick: Optional[int]
    text: Optional[str]  # e.g. "crescendo"

    possible_tags: ClassVar[list[str]] = ["tick", "html-data"]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Dynamic":
        assert tag.name == "Dynamic"
        note_possible_tags(cls, tag)
        style_tag = tag.find("style", recursive=False)
        style = None if style_tag is None else int(style_tag.text)
        subtype = tag.find("subtype", recursive=False).text
        velocity_tag = tag.find("velocity", recursive=False)
        velocity = None if velocity_tag is None else int(velocity_tag.text)
        track_tag = tag.find("track", recursive=False)
        track = None if track_tag is None else int(track_tag.text)
        # tick_tag = tag.find("tick", recursive=False)
        # tick = None if tick_tag is None else int(tick_tag.text)
        html_data_tag = tag.find("html-data", recursive=False)
        html_text = None if html_data_tag is None else html_data_tag.find("body").get_text(strip=True)
        text_tag = tag.find("text", recursive=False)
        text = html_text if text_tag is None else text_tag.text
        return cls(style=style, subtype=subtype, velocity=velocity, track=track, text=text)


@define
class StaffText:
    # <StaffText>
    #   <channelSwitch voice="0" name="normal"/>
    #   <channelSwitch voice="1" name="normal"/>
    #   <pos x="0.274464" y="-5.64678"/>
    #   <text><i>normal</i></text>
    #   </StaffText>
    style: Optional[str]
    pos_x: Optional[float]
    pos_y: Optional[float]
    text: str

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "StaffText":
        assert tag.name == "StaffText"
        pos_tag = tag.find("pos", recursive=False)
        pos_x = None if pos_tag is None else float(pos_tag.get("x"))
        pos_y = None if pos_tag is None else float(pos_tag.get("y"))
        text = tag.find("text", recursive=False).text
        style_tag = tag.find("style", recursive=False)
        style = None if style_tag is None else style_tag.text
        return cls(style=style, pos_x=pos_x, pos_y=pos_y, text=text)


@define
class Clef:
    concertClefType: str  # known values: "C4", "F", "C3", "G"
    transposingClefType: str  # known values: "C4", "F", "C3", "G"

    possible_tags: ClassVar[list[str]] = ["subtype"]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Clef":
        assert tag.name == "Clef"
        note_possible_tags(cls, tag)
        # subtype_tag = tag.find("subtype", recursive=False)
        # subtype = None if subtype_tag is None else subtype_tag.text
        concertClefType = tag.find("concertClefType", recursive=False).text
        transposingClefType = tag.find("transposingClefType", recursive=False).text
        return cls(concertClefType=concertClefType, transposingClefType=transposingClefType)

    @property
    def name(self) -> str:
        # see https://en.wikipedia.org/wiki/Clef
        assert self.concertClefType == self.transposingClefType
        if self.concertClefType == "G":
            return "Treble"
        if self.concertClefType == "F":
            return "Bass"
        if self.concertClefType == "C3":
            return "Alto"
        if self.concertClefType == "C4":
            return "Tenor"
        return f"Unknown {self}"


@define
class Tuplet:
    # Define with an "id" (Chords and Rests usually comes after all definitions in the Measure)
    # attributes
    id: str

    # child elements
    track: Optional[int]  # known values: 1, 2
    # tick: Optional[int]
    # numberType: Optional[int]  # known values: 0
    # bracketType: Optional[int]  # known values: 0
    normalNotes: int  # known values: 6 !important
    actualNotes: int  # known values: 11 !important
    baseNote: str  # known values: "eight", ... !important
    number: Optional["Number"]

    possible_tags: ClassVar[list[str]] = ["numberType", "bracketType", "tick"]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Tuplet":
        assert tag.name == "Tuplet"
        note_possible_tags(cls, tag)
        id_ = int(tag.get("id"))
        track_tag = tag.find("track", recursive=False)
        track = None if track_tag is None else int(track_tag.text)
        # tick_tag = tag.find("tick", recursive=False)
        # tick = None if tick_tag is None else int(tick_tag.text)
        # numberType_tag = tag.find("numberType", recursive=False)
        # numberType = None if numberType_tag is None else int(numberType_tag.text)
        # bracketType_tag = tag.find("bracketType", recursive=False)
        # bracketType = int(bracketType_tag.text)
        normalNotes = int(tag.find("normalNotes", recursive=False).text)
        actualNotes = int(tag.find("actualNotes", recursive=False).text)
        baseNote = tag.find("baseNote", recursive=False).text
        number_tag = tag.find("Number", recursive=False)
        number = None if number_tag is None else Number.from_tag(number_tag)

        return cls(
            id=id_,
            track=track,
            # tick=tick,
            # numberType=numberType,
            # bracketType=bracketType,
            normalNotes=normalNotes,
            actualNotes=actualNotes,
            baseNote=baseNote,
            number=number,
        )


@define
class Number:
    style: int  # known values: "Tuplet"
    # subtype: str  # known values:
    text: int

    possible_tags: ClassVar[list[str]] = ["subtype"]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Number":
        assert tag.name == "Number"
        note_possible_tags(cls, tag)
        style = int(tag.find("style", recursive=False).text)
        assert style == "Tuplet"
        # subtype = tag.find("subtype", recursive=False).text
        text = int(tag.find("text", recursive=False).text)
        return cls(style=style, text=text)


@define
class Harmony:
    # Latches onto the next Rest/Chord
    # E7/A -> root,name,base = 18,7,17
    root: int  # known values: 13-F,14-C, 15-G, 16-D, 17-A, 18-E, 19-B
    name: Optional[str]  # known values: "m", "7"
    base: Optional[int]  # known values: same as root
    play: Optional[bool]  # known values: "0"

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Harmony":
        assert tag.name == "Harmony"

        root = int(tag.find("root", recursive=False).text)
        name_tag = tag.find("name", recursive=False)
        name = None if name_tag is None else name_tag.text
        base_tag = tag.find("base", recursive=False)
        base = None if base_tag is None else int(base_tag.text)
        play_tag = tag.find("play", recursive=False)
        play = None if play_tag is None else bool(int(play_tag.text))

        return cls(root=root, name=name, base=base, play=play)


@define
class Rest:
    visible: Optional[bool]
    # tick: Optional[int]
    durationType: str  # known values: "measure", "whole", "half", "quarter", "eight", "16th", "32nd", "64th", "128th"
    duration: Optional["Rest.Duration"]  # new in v2  # used with "measure"
    dots: int
    articulation: Optional["Articulation"]  # fermata

    possible_tags: ClassVar[list[str]] = ["tick"]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Rest":
        assert tag.name == "Rest"
        note_possible_tags(cls, tag)
        visible_tag = tag.find("visible", recursive=False)
        visible = None if visible_tag is None else bool(int(visible_tag.text))
        # tick_tag = tag.find("tick", recursive=False)
        # tick = None if tick_tag is None else int(tick_tag.text)
        dots_tag = tag.find("dots", recursive=False)
        dots = 0 if dots_tag is None else int(dots_tag.text)
        durationType = tag.find("durationType", recursive=False).text
        duration_tag = tag.find("duration", recursive=False)
        assert durationType != "measure" or duration_tag is not None
        duration = None if duration_tag is None else cls.Duration.from_tag(duration_tag)
        articulation_tag = tag.find("Articulation")
        articulation = None if articulation_tag is None else Articulation.from_tag(articulation_tag)
        return cls(
            visible=visible,
            # tick=tick,
            durationType=durationType,
            duration=duration,
            dots=dots,
            articulation=articulation,
        )

    @property
    def pulsation(self) -> float:
        if self.durationType == "measure":
            return tick_length_to_pulsation(self.duration.tick_length)
        return get_pulsation(self.durationType, self.dots)

    @property
    def tick_length(self) -> int:
        if self.durationType == "measure":
            return self.duration.tick_length
        return get_tick_length(self.durationType, self.dots)

    @define
    class Duration:
        # self-defined attribs
        nominator: int
        denominator: int

        @classmethod
        def from_tag(cls, tag: bs4.element.Tag) -> "Rest.Duration":
            assert tag.name == "duration"
            nominator, denominator = map(int, tag.text.split("/"))
            return cls(nominator=nominator, denominator=denominator)

        @property
        def tick_length(self) -> int:
            return get_tick_length(get_duration_type(self.denominator)) * self.nominator


@define
class Chord:
    track: Optional[int]  # v2.06 known values: 1, 16
    # tick: Optional[int]
    tuplet_id: Optional[int]  # matches outside Tuplet
    dots: int  # 0 if None
    durationType: str  # known values: "whole", "half", "quarter", "eight", "16th", "32nd", "64th", "128th"
    beam_id: Optional[int]  # matches outside Beam
    # lyrics: Optional[str]
    slur: Optional["Chord.Slur"]  # id matches outside Slur
    appoggiatura: bool  # if exists, true and is not a whole note
    notes: list["Note"]
    articulation: Optional["Articulation"]
    arpeggio: Optional["Arpeggio"]
    tremolo: Optional["Tremolo"]

    possible_tags: ClassVar[list[str]] = ["tick"]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Chord":
        assert tag.name == "Chord"
        note_possible_tags(cls, tag)
        track_tag = tag.find("track", recursive=False)
        track = None if track_tag is None else int(track_tag.text)
        # tick_tag = tag.find("tick", recursive=False)
        # tick = None if tick_tag is None else int(tick_tag.text)
        tuplet_tag = tag.find("Tuplet", recursive=False)
        tuplet_id = None if tuplet_tag is None else int(tuplet_tag.text)
        beam_tag = tag.find("Beam", recursive=False)
        beam_id = None if beam_tag is None else int(beam_tag.text)
        dots_tag = tag.find("dots", recursive=False)
        dots = 0 if dots_tag is None else int(dots_tag.text)
        durationType = tag.find("durationType", recursive=False).text

        slur_tag = tag.find("Slur", recursive=False)
        slur = None if slur_tag is None else cls.Slur.from_tag(slur_tag)
        appoggiatura = tag.find("appoggiatura", recursive=False) is not None

        notes = list(map(Note.from_tag, tag.find_all("Note", recursive=False)))

        articulation_tag = tag.find("Articulation", recursive=False)
        articulation = None if articulation_tag is None else Articulation.from_tag(articulation_tag)
        arpeggio_tag = tag.find("Arpeggio", recursive=False)
        arpeggio = None if arpeggio_tag is None else Arpeggio.from_tag(arpeggio_tag)
        tremolo_tag = tag.find("Tremolo", recursive=False)
        tremolo = None if tremolo_tag is None else Tremolo.from_tag(tremolo_tag)

        return cls(
            track=track,
            # tick=tick,
            tuplet_id=tuplet_id,
            beam_id=beam_id,
            dots=dots,
            durationType=durationType,
            slur=slur,
            appoggiatura=appoggiatura,
            notes=notes,
            articulation=articulation,
            arpeggio=arpeggio,
            tremolo=tremolo,
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
    class Slur:
        # attributes
        type: str  # known values: "start", "stop"
        id: int  # id linked with Slur (v2 in same measure)

        @classmethod
        def from_tag(cls, tag: bs4.element.Tag) -> "Chord.Slur":
            assert tag.name == "Slur"
            type_ = tag.get("type")
            id_ = int(tag.get("id"))
            return cls(type=type_, id=id_)


@define
class Slur:
    # attributes
    id: int
    # child elements
    track: int

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Slur":
        assert tag.name == "Slur"
        id_ = int(tag.get("id"))
        track_tag = tag.find("track", recursive=False)
        track = int(track_tag.text)
        return cls(id=id_, track=track)


@define
class Articulation:
    subtype: str  # known values: "staccato", "sforzato", "fermata"  # linked with Part.Instrument.Articulation
    track: Optional[int]

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Articulation":
        assert tag.name == "Articulation"
        subtype_tag = tag.find("subtype", recursive=False)
        assert subtype_tag is not None, tag
        subtype = None if subtype_tag is None else subtype_tag.text
        track_tag = tag.find("track", recursive=False)
        track = None if track_tag is None else int(track_tag.text)
        return cls(subtype=subtype, track=track)


@define
class Arpeggio:  # TODO: find example in v2
    track: Optional[int]
    userLen1: Optional[float]
    subtype: int

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Arpeggio":
        assert tag.name == "Arpeggio"
        track_tag = tag.find("track", recursive=False)
        track = None if track_tag is None else int(track_tag.text)
        userLen1_tag = tag.find("userLen1", recursive=False)
        userLen1 = None if userLen1_tag is None else float(userLen1_tag.text)
        subtype_tag = tag.find("subtype", recursive=False)
        subtype = None if subtype_tag is None else int(subtype_tag.text)
        assert subtype is not None
        return cls(track=track, userLen1=userLen1, subtype=subtype)


@define
class Tremolo:
    subtype: str  # known values: r32

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Tremolo":
        assert tag.name == "Tremolo"
        subtype = tag.find("subtype").text
        return cls(subtype=subtype)


@define
class Note:
    track: Optional[int]
    visible: Optional[bool]
    tie_id: Optional[int]  # matches with Note.endSpanner (not Measure.endSpanner)
    endSpanner_id: Optional[int]  # matches with Note.Tie
    pitch: int  # MIDI note number https://en.wikipedia.org/wiki/Scientific_pitch_notation#Table_of_note_frequencies
    tpc: int
    tpc2: Optional[int]  # new in v2 (?)
    accidental: Optional["Accidental"]
    symbol: Optional["Symbol"]
    veloType: Optional[str]  # known values: "user"
    velocity: Optional[int]
    # TODO: Check fingering for v1/2
    fingering: Optional[int]  # new? # known values: 1

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Note":
        assert tag.name == "Note"
        track_tag = tag.find("track", recursive=False)
        track = None if track_tag is None else int(track_tag.text)
        visible_tag = tag.find("visible", recursive=False)
        visible = None if visible_tag is None else bool(int(visible_tag.text))

        pitch = int(tag.find("pitch", recursive=False).text)
        tpc = int(tag.find("tpc", recursive=False).text)
        tpc2_tag = tag.find("tpc2", recursive=False)
        tpc2 = None if tpc2_tag is None else int(tpc2_tag.text)
        tie_tag = tag.find("Tie", recursive=False)
        tie_id = None if tie_tag is None else int(tie_tag.get("id"))
        endSpanner_tag = tag.find("endSpanner", recursive=False)
        endSpanner_id = None if endSpanner_tag is None else int(endSpanner_tag.get("id"))

        accidental_tag = tag.find("Accidental", recursive=False)
        accidental = None if accidental_tag is None else Accidental.from_tag(accidental_tag)
        symbol_tag = tag.find("Symbol", recursive=False)
        symbol = None if symbol_tag is None else Symbol.from_tag(symbol_tag)
        veloType_tag = tag.find("veloType", recursive=False)
        veloType = None if veloType_tag is None else veloType_tag.text
        velocity_tag = tag.find("velocity", recursive=False)
        velocity = None if velocity_tag is None else int(velocity_tag.text)
        fingering_tag = tag.find("Fingering", recursive=False)
        fingering = None if fingering_tag is None else int(fingering_tag.find("text", recursive=False).text)
        return cls(
            track=track,
            visible=visible,
            tie_id=tie_id,
            endSpanner_id=endSpanner_id,
            pitch=pitch,
            tpc=tpc,
            tpc2=tpc2,
            accidental=accidental,
            symbol=symbol,
            veloType=veloType,
            velocity=velocity,
            fingering=fingering,
        )

    @property
    def tie(self) -> bool:
        # TODO: maybe remove this prop
        return self.tie_id is not None


@define
class Symbol:  # TODO: Find v2 example
    name: str  # known values: "pedalasterisk" (v1) "pedal ped"

    @classmethod
    def from_tag(cls, tag: bs4.element.Tag) -> "Symbol":
        assert tag.name == "Symbol"
        name = tag.find("name", recursive=False).text
        return cls(name=name)


@define
class Accidental:
    subtype: str  # known values: "sharp", "flat", "natural", "double sharp", "double flat"
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
