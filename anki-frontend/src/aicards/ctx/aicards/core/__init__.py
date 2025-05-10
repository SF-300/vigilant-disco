import asyncio as aio
import random
import uuid
import typing as t

import aioreactive as rx

from ..base import (
    IOperation,
    Image,
    Example,
    IService,
    Extraction,
    Protonote,
    ExtractionWithPrototonotes,
    MeaningProtonote,
    EnglishNounProtonote,
    LlmChatMessage,
)


class Operation[R](IOperation[R]):
    def __init__(
        self,
        coro: t.Coroutine[t.Any, R, t.Any],
        llm_messages: rx.AsyncObservable[LlmChatMessage],
    ):
        self._task = aio.create_task(coro)
        self._llm_messages = llm_messages

    @property
    def llm_messages(self) -> rx.AsyncObservable[LlmChatMessage]:
        return self._llm_messages

    def __await__(self):
        return self._task.__await__()


class Service(IService):
    def process_image(self, image: Image) -> Operation[list[Extraction]]:
        llm_messages = rx.AsyncSubject()
        return Operation(
            self._process_image(image, llm_messages),
            llm_messages,
        )

    async def _process_image(
        self,
        image: Image,
        llm_messages: rx.AsyncSubject,
    ) -> list[Extraction]:
        await llm_messages.asend(
            LlmChatMessage(
                role="user",
                text=f"Process image {image.name} with mime type {image.mime}",
            )
        )
        return [
            Extraction(
                id=f"extraction-{uuid.uuid4()}",
                snippet=f"Snippet {random.randint(1, 100)}",
                reason=f"Reason {random.randint(1, 100)}",
            )
            for _ in range(random.randint(1, 5))
        ]

    def create_protonotes(
        self,
        extractions: t.Sequence[Extraction],
    ) -> Operation[t.Sequence[ExtractionWithPrototonotes]]:
        llm_messages = rx.AsyncSubject()
        return Operation(
            self._create_protonotes(extractions, llm_messages),
            llm_messages,
        )

    async def _create_protonotes(
        self,
        extractions: t.Sequence[Extraction],
        llm_messages: rx.AsyncSubject,
    ) -> t.Sequence[ExtractionWithPrototonotes]:
        await llm_messages.asend(
            LlmChatMessage(
                role="user",
                text=f"Create protonotes for {len(extractions)} extractions",
            )
        )
        return [
            ExtractionWithPrototonotes(
                extraction=extraction,
                protonotes=(
                    MeaningProtonote(
                        id=f"proto-{uuid.uuid4()}",
                        type="Meaning",
                        concept=f"Concept {random.randint(10, 99)}",
                        examples=(
                            Example(
                                sentence="Example sentence 1",
                                image=None,
                            ),
                            None,
                        ),
                    ),
                    EnglishNounProtonote(
                        id=f"proto-{uuid.uuid4()}",
                        type="English Noun",
                        singular=f"Word {random.randint(10, 99)}",
                        plural="cards",
                    ),
                ),
            )
            for extraction in extractions
        ]

    def export_protonotes(
        self,
        protonotes: t.Sequence[Protonote],
    ) -> Operation[t.Sequence[Protonote]]:
        llm_messages = rx.AsyncSubject()
        return Operation(
            self._export_protonotes(protonotes, llm_messages),
            llm_messages,
        )

    async def _export_protonotes(
        self,
        protonotes: t.Sequence[Protonote],
        llm_messages: rx.AsyncSubject,
    ) -> bool:
        await llm_messages.asend(
            LlmChatMessage(
                role="user",
                text=f"Export {len(protonotes)} protonotes",
            )
        )
        return True
