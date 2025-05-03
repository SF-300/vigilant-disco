import typing as t
from abc import ABC

from pydantic.dataclasses import dataclass


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
class Example:
    sentence: str
    image: None


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
    examples: tuple[
        Example | None,
        Example | None,
        # Example | None,
        # Example | None,
        # Example | None,
    ]

    @property
    def description(self) -> str:
        return self.concept


@dataclass(frozen=True)
class EnglishNounProtonote(Protonote):
    type: t.Literal["English Noun"]
    singular: str
    plural: str

    @property
    def description(self) -> str:
        return f"English noun {self.singular}"


@dataclass(frozen=True)
class ExtractionWithPrototonotes:
    extraction: Extraction
    protonotes: tuple[Protonote, ...]


class Service(ABC):
    async def process_image(self, image: Image) -> t.Sequence[Extraction]: ...

    async def create_protonotes(
        self, extractions: t.Sequence[Extraction]
    ) -> t.Sequence[ExtractionWithPrototonotes]: ...

    async def export_protonotes(self, protonotes: t.Sequence[Protonote]) -> bool: ...
