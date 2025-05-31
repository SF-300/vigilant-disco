from dataclasses import dataclass
import logging
import typing as t
from enum import StrEnum

from frozendict import frozendict


class RecordAttr(StrEnum):
    RAW_SPANS = "spans"
    SPANS_IDS = "spans_ids"
    SPANS_MSGS = "spans_msgs"
    SPANS_MESSAGES = "spans_messages"


type Level = t.Literal["debug", "info", "warning", "error", "critical"] | int
type Msg = t.LiteralString
type ExcInfo = BaseException
type InContext = t.Mapping[str, t.Any]
type NativeLogger = logging.Logger | logging.LoggerAdapter


@dataclass(frozen=True, slots=True)
class Span:
    id: str
    name: str
    context: frozendict[str, t.Any] = frozendict()


class SpanDict(t.TypedDict):
    id: str
    msg: str
    message: str
    context: t.Mapping[str, t.Any]


class SpannerLike[V: LoggerLike](t.Protocol):
    def __enter__(self) -> V: ...
    def __exit__(self, *args, **kwargs) -> bool | None: ...
    def __call__[**P, R](
        self,
        f: t.Callable[P, R],
        /,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R: ...


@t.runtime_checkable
class LoggerLike(t.Protocol):
    def log(
        self,
        level: Level,
        msg: Msg,
        context: InContext = ...,
        /,
        exc_info: ExcInfo = ...,
        stacklevel: int = ...,
    ) -> None: ...

    def debug(
        self,
        msg: Msg,
        context: InContext = ...,
        /,
        exc_info: Exception = ...,
        stacklevel: int = ...,
    ): ...

    def info(
        self,
        msg: Msg,
        context: InContext = ...,
        /,
        exc_info: Exception = ...,
        stacklevel: int = ...,
    ): ...

    def warn(
        self,
        msg: Msg,
        context: InContext = ...,
        /,
        exc_info: Exception = ...,
        stacklevel: int = ...,
    ): ...

    def error(
        self,
        msg: Msg,
        context: InContext = ...,
        /,
        exc_info: Exception = ...,
        stacklevel: int = ...,
    ): ...

    def critical(
        self,
        msg: Msg,
        context: InContext = ...,
        /,
        exc_info: Exception = ...,
        stacklevel: int = ...,
    ): ...

    def span(
        self,
        msg: Msg,
        context: InContext = ...,
        /,
        sid: str = ...,
    ) -> SpannerLike: ...
