import typing as t

from aicards.ctx.aicards.base import LlmChatMessage


class AddLlmChatMessage(t.Protocol):
    async def __call__(self, msg: LlmChatMessage) -> None: ...
