import asyncio
import typing as t

from aicards.ctx.aicards.base import Service, ExtractionWithPrototonotes


async def export_handler(
    export_q: asyncio.Queue[t.Sequence[ExtractionWithPrototonotes]],
    service: Service,
) -> None:
    while True:
        items = await export_q.get()

        await service.export_protonotes([p for ep in items for p in ep.protonotes])