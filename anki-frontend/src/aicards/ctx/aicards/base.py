import typing as t
from abc import ABC

import aioreactive as rx
import pydantic
from pydantic.dataclasses import dataclass

from aicards.misc.logging import LoggerLike


@dataclass(frozen=True)
class Image:
    name: str
    mime: str
    data: bytes


@dataclass(frozen=True)
class Extraction:
    """
    "Single logical emphasis from the image"
    """

    reason: str = pydantic.Field(
        description="Presumptive reason why user might want to make this snippet into Anki notes/cards",
    )
    snippet: str = pydantic.Field(
        description="What user has actually emphasized in the image",
    )
    context: str | None = pydantic.Field(
        description="Context for the snippet, if any",
        default=None,
    )
    comment: str | None = pydantic.Field(
        description="Optional comment for LLM during downstream processing stages",
        default=None,
    )


@dataclass(frozen=True)
class Example:
    sentence: str
    image: None


@dataclass(frozen=True)
class Protonote(ABC):
    id: str
    type: str

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
    def extract_emphases(
        self,
        image: Image,
        logger: LoggerLike = ...,
    ) -> IOperation[list[Extraction]]: ...

    def create_protonotes(
        self,
        extractions: t.Sequence[Extraction],
        logger: LoggerLike = ...,
    ) -> IOperation[list[ExtractionWithPrototonotes]]: ...

    def export_protonotes(
        self,
        protonotes: list[Protonote],
        logger: LoggerLike = ...,
    ) -> IOperation[bool]: ...
