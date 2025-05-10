import asyncio as aio
import random
import uuid
import typing as t

import aioreactive as rx

from ..base import (
    Image,
    Example,
    Service,
    Extraction,
    Protonote,
    ExtractionWithPrototonotes,
    MeaningProtonote,
    EnglishNounProtonote,
    LlmChatMessage,
)


class ImageProcessing(t.Awaitable[t.Sequence[Extraction]]):
    def __init__(self, image: Image):
        self._llm_messages = rx.AsyncSubject()

        async def process_impl():
            await self._llm_messages.asend(
                LlmChatMessage(
                    role="user",
                    text=f"Process image {image.name} with mime type {image.mime}",
                )
            )
            return [
                Extraction(
                    id=f"extraction-{uuid.uuid4()}",
                    snippet=f"Snippet {random.randint(1, 100)}",
                    context=None,
                )
                for _ in range(random.randint(1, 5))
            ]

        self._task = aio.create_task(process_impl())

    @property
    def llm_messages(self) -> rx.AsyncObservable:
        return self._llm_messages

    def __await__(self):
        return self._task.__await__()


class ProtonotesCreation(t.Awaitable[t.Sequence[ExtractionWithPrototonotes]]):
    def __init__(self, extractions: t.Sequence[Extraction]):
        self._llm_messages = rx.AsyncSubject()

        async def impl() -> t.Sequence[ExtractionWithPrototonotes]:
            await self._llm_messages.asend(
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

        self._task = aio.create_task(impl())

    @property
    def llm_messages(self) -> rx.AsyncObservable:
        return self._llm_messages

    def __await__(self):
        return self._task.__await__()


class ProtonotesExporting(t.Awaitable[bool]):
    def __init__(self, protonotes: t.Sequence[Protonote]):
        self._llm_messages = rx.AsyncSubject()

        async def impl() -> bool:
            await self._llm_messages.asend(
                LlmChatMessage(
                    role="user",
                    text=f"Export {len(protonotes)} protonotes",
                )
            )
            return True

        self._task = aio.create_task(impl())

    @property
    def llm_messages(self) -> rx.AsyncObservable:
        return self._llm_messages

    def __await__(self):
        return self._task.__await__()


class MockService(Service):
    def process_image(
        self,
        image: Image,
    ) -> ImageProcessing:
        return ImageProcessing(image)

    def create_protonotes(
        self, extractions: t.Sequence[Extraction]
    ) -> ProtonotesCreation:
        return ProtonotesCreation(extractions)

    def export_protonotes(
        self, protonotes: t.Sequence[Protonote]
    ) -> ProtonotesExporting:
        return ProtonotesExporting(protonotes)
