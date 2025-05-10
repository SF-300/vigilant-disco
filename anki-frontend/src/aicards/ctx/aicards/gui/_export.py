import asyncio
import typing as t

from aicards.ctx.aicards.base import IService, ExtractionWithPrototonotes

from ._base import AddLlmChatMessage


async def export_handler(
    export_q: asyncio.Queue[t.Sequence[ExtractionWithPrototonotes]],
    service: IService,
    add_llm_chat_message: AddLlmChatMessage,
) -> None:
    while True:
        items = await export_q.get()

        exporting = service.export_protonotes(
            [p for ep in items for p in ep.protonotes]
        )
        async with await exporting.llm_messages.subscribe_async(add_llm_chat_message):
            await exporting
