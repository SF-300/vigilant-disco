import base64
import typing as t
import contextlib
from dataclasses import dataclass as native_dataclass

import pydantic
from openai import AsyncOpenAI
from pydantic.dataclasses import dataclass

from aicards.ctx.aicards.base import Extraction, Image, Protonote


@dataclass(frozen=True)
class ExtractionResult:
    message: str = pydantic.Field(
        description="User-friendly message to be shown to the user for this processing stage in the chat view/log",
    )
    extractions: tuple[Extraction, ...]


@dataclass(frozen=True)
class ProtonotesGenerationResult:
    message: str = pydantic.Field(
        description="User-friendly message to be shown to the user for this processing stage in the chat view/log",
    )
    protonotes: tuple[Protonote, ...]


@native_dataclass(frozen=True)
class AiClient:
    @classmethod
    @contextlib.asynccontextmanager
    async def running(cls, client: AsyncOpenAI) -> t.AsyncIterator[t.Self]:
        yield cls(client)

    _client: AsyncOpenAI

    async def get_extractions_from_image(
        self,
        image: Image,
    ) -> ExtractionResult:
        prompt = ""
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
                            "image_url": {"url": f"data:image/png;base64,{b64_image}"},
                        },
                    ],
                }
            ],
        )

    async def generate_protonotes(
        self,
        extractions: t.Sequence[Extraction],
    ) -> ProtonotesGenerationResult:
        raise NotImplementedError()


def _to_base64_image(image: Image) -> str:
    return base64.b64encode(image.data).decode("utf-8")
