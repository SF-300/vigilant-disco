import typing as t
from abc import ABC

import aioreactive as rx
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


@dataclass(frozen=True)
class LlmChatMessage:
    role: str
    text: str


class IOperation[R](t.Awaitable[R]):
    llm_messages: rx.AsyncObservable[LlmChatMessage]


class IService(ABC):
    def process_image(
        self,
        image: Image,
    ) -> IOperation[list[Extraction]]: ...

    def create_protonotes(
        self,
        extractions: t.Sequence[Extraction],
    ) -> IOperation[list[ExtractionWithPrototonotes]]: ...

    def export_protonotes(
        self,
        protonotes: list[Protonote],
    ) -> IOperation[bool]: ...
