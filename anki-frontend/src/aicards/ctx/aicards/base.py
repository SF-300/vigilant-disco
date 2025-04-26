import typing as t
from abc import ABC
from dataclasses import dataclass


@dataclass(frozen=True)
class Image:
    name: str
    mime: str
    data: bytes


@dataclass(frozen=True)
class Extraction:
    id: str
    snippet: str
    context: str | None


@dataclass(frozen=True)
class Protonote:
    id: str

    @property
    def description(self) -> str:
        raise NotImplementedError()


@dataclass(frozen=True)
class MeaningProtonote(Protonote):
    type: t.Literal["Meaning"]
    concept: str
    examples: tuple[str, ...]

    @property
    def description(self) -> str:
        return f"Meaning of {self.concept} in the context of {self.id}"


@dataclass(frozen=True)
class EnglishNounProtonote(Protonote):
    type: t.Literal["English Noun"]
    singular: str
    plural: str
    examples: tuple[str, ...]

    @property
    def description(self) -> str:
        return f"English noun {self.singular}"


@dataclass(frozen=True)
class ExtractionProtonotes:
    extraction: Extraction
    protonotes: tuple[Protonote]


class Service(ABC):
    def process_image(self, image: Image) -> t.Sequence[Extraction]: ...

    def create_protonotes(
        self, extractions: t.Sequence[Extraction]
    ) -> t.Sequence[ExtractionProtonotes]: ...

    def export_protonotes(self, protonotes: t.Sequence[Protonote]) -> bool: ...
