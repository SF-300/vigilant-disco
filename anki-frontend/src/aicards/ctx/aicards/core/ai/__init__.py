import asyncio as aio
import base64
import json
import textwrap
import typing as t
import contextlib
from dataclasses import dataclass as native_dataclass

import pydantic
import openai
import openai.types.chat
from openai import AsyncOpenAI
from pydantic.dataclasses import dataclass

from aicards.ctx.aicards.base import Extraction, Image, Protonote


@dataclass(frozen=True)
class ExtractionResult:
    message: str = pydantic.Field(
        description="User-friendly message to be shown to the user for this processing stage in the chat view/log",
    )
    extractions: tuple[Extraction, ...] = pydantic.Field()


@dataclass(frozen=True)
class ProtonotesGenerationResult:
    message: str = pydantic.Field(
        description="User-friendly message to be shown to the user for this processing stage in the chat view/log",
    )
    protonotes: tuple[Protonote, ...] = pydantic.Field()


class AiResponse[R](t.Awaitable[R]):
    def __init__(self, prompt: str, coro: t.Coroutine[t.Any, R, t.Any]) -> None:
        self._prompt = prompt
        self._result = aio.create_task(coro)

    @property
    def prompt(self) -> str:
        return self._prompt

    def __await__(self):
        return self._result.__await__()


_extraction_json_schema = json.dumps(
    pydantic.TypeAdapter(Extraction).json_schema(),
    indent=2,
    ensure_ascii=False,
    # most concise format
    separators=(",", ": "),
)


@native_dataclass(frozen=True)
class AiClient:
    @classmethod
    @contextlib.asynccontextmanager
    async def running(cls, client: AsyncOpenAI) -> t.AsyncIterator[t.Self]:
        yield cls(client)

    _client: AsyncOpenAI

    def get_extractions_from_image(
        self,
        image: Image,
    ) -> AiResponse[ExtractionResult]:
        # fmt: off
        prompt = textwrap.dedent(f"""\
        From this image, extract the information user has emphasized and wants to memorize for his language learning.                
        Your request must adhere to the following schema: {_extraction_json_schema}
        """.strip()
        )
        # fmt: on

        async def impl():
            return ExtractionResult(
                message="test",
                extractions=(
                    Extraction(
                        reason="test",
                        snippet="test",
                        context=None,
                        comment=None,
                    ),
                ),
            )
            b64_image = _to_base64_image(image)
            # Call the OpenAI API
            response = await self._client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{b64_image}"
                                },
                            },
                        ],
                    }
                ],
            )

        return AiResponse(prompt, impl())

    async def generate_protonotes(
        self,
        extractions: t.Sequence[Extraction],
    ) -> ProtonotesGenerationResult:
        raise NotImplementedError()


def _to_base64_image(image: Image) -> str:
    return base64.b64encode(image.data).decode("utf-8")
