from typing import Protocol, Iterable

import bs4.element


class ProtoNote(Protocol):
    pitch: int


class ProtoChord(Protocol):
    notes: Iterable[ProtoNote]


class WithPossibleTags(Protocol):
    possible_tags: list[str]


def note_possible_tags(cls: WithPossibleTags, tag: bs4.element.Tag):
    for name in cls.possible_tags:
        if tag.find(name, recursive=False) is not None:
            print(f"FOUND TAG: {name} in <{cls.__name__}>")
            print(tag.prettify())
