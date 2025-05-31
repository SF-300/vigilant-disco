import asyncio as aio
import contextlib
import random
import uuid
import typing as t
from dataclasses import dataclass as native_dataclass

import aioreactive as rx

from aicards.misc.logging import LoggerLike, null_logger
from aicards.misc.ankiconnect_client import AnkiConnectClient

from aicards.ctx.ankiconnect import notedata_from
from aicards.ctx.aicards.base import (
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
from aicards.ctx.aicards.core.ai import AiClient


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


@native_dataclass(frozen=True)
class Service(IService):
    @classmethod
    @contextlib.asynccontextmanager
    async def running(
        cls,
        ai_client: AiClient,
        anki_client: AnkiConnectClient,
        deck_name: str = "Default",
        logger: LoggerLike = null_logger,
    ) -> t.AsyncIterator[t.Self]:
        yield cls(
            ai_client,
            anki_client,
            deck_name,
            logger,
        )

    _ai_client: AiClient
    _anki_client: AnkiConnectClient
    _deck_name: str
    _logger: LoggerLike

    def extract_emphases(
        self, image: Image, logger: LoggerLike = null_logger
    ) -> Operation[list[Extraction]]:
        llm_messages = rx.AsyncSubject()
        return Operation(
            self._extract_emphases(image, llm_messages),
            llm_messages,
        )

    async def _extract_emphases(
        self,
        image: Image,
        llm_messages: rx.AsyncSubject,
    ) -> list[Extraction]:
        result = self._ai_client.get_extractions_from_image(image)

        await llm_messages.asend(
            LlmChatMessage(
                role="user",
                text=result.prompt,
            )
        )

        return list((await result).extractions)

    def create_protonotes(
        self,
        extractions: t.Sequence[Extraction],
        logger: LoggerLike = null_logger,
    ) -> Operation[t.Sequence[ExtractionWithPrototonotes]]:
        llm_messages = rx.AsyncSubject()
        return Operation(
            self._create_protonotes(extractions, llm_messages, logger),
            llm_messages,
        )

    async def _create_protonotes(
        self,
        extractions: t.Sequence[Extraction],
        llm_messages: rx.AsyncSubject,
        logger: LoggerLike,
    ) -> t.Sequence[ExtractionWithPrototonotes]:
        await llm_messages.asend(
            LlmChatMessage(
                role="user",
                text=f"Create protonotes for {len(extractions)} extractions",
            )
        )

        results = [
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
                        singular=f"Singular {random.randint(10, 99)}",
                        plural="Plural",
                    ),
                ),
            )
            for extraction in extractions
        ]

        return results

    def export_protonotes(
        self,
        protonotes: t.Sequence[Protonote],
        logger: LoggerLike = null_logger,
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
        for protonote in protonotes:
            await llm_messages.asend(
                LlmChatMessage(
                    role="user",
                    text=f"Exporting protonote {protonote.description}",
                )
            )
            note_data = notedata_from(protonote, deck_name="English")
            await self._anki_client.add_note(note_data)
        return True
