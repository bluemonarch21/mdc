from typing import Any, Iterable, Iterator, Optional, Protocol, Union

import bs4.element


class Tempo(Protocol):
    tempo: float
    tick: int


class Note(Protocol):
    pitch: int
    accidental: Optional[Any]
    tie: bool


class Stroke(Protocol):
    durationType: str
    dots: int


class Chord(Stroke):
    notes: Iterable[Note]


class Rest(Stroke):
    pass


class Measure(Protocol):
    strokes: list[Stroke]
    stroke_ticks: set[int]  # TODO: Use numpy array instead

    def get_stroke_tick(stroke: Stroke) -> int:
        ...


class Staff(Protocol):
    id: int
    notes: Iterator[Note]
    measures: list[Measure]

    def get_average_pitch(self) -> float:
        ...

    def get_hand_displacement_rate(self) -> float:
        ...

    def get_playing_speed(self) -> float:
        ...

    def get_polyphony_rate(self) -> float:
        ...


class Identified(Protocol):
    id: int


class Part(Protocol):
    is_piano: bool
    staffs: list[Union[Identified, object]]
    instrument: object


class WithPossibleTags(Protocol):
    possible_tags: list[str]


def note_possible_tags(cls: WithPossibleTags, tag: bs4.element.Tag):
    for name in cls.possible_tags:
        if tag.find(name, recursive=False) is not None:
            print(f"FOUND TAG: {name} in <{cls.__name__}>")
            print(tag.prettify())
