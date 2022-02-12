from typing import Any, Iterable, Iterator, Optional, Protocol, Union

import bs4.element


class Note(Protocol):
    pitch: int
    accidental: Optional[Any]


class Chord(Protocol):
    notes: Iterable[Note]


class Measure(Protocol):
    stroke_ticks: set[int]  # TODO: Use numpy array instead


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
    staffs: list[Union[Identified, Protocol]]


class WithPossibleTags(Protocol):
    possible_tags: list[str]


def note_possible_tags(cls: WithPossibleTags, tag: bs4.element.Tag):
    for name in cls.possible_tags:
        if tag.find(name, recursive=False) is not None:
            print(f"FOUND TAG: {name} in <{cls.__name__}>")
            print(tag.prettify())
