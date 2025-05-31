import typing as t
import logging

from frozendict import frozendict

from .base import NativeLogger, RecordAttr, Span
from .core import LoggerWrapper, spanner_contextmanager

type InContext = frozendict[str, t.Any]
type InSpans = tuple[Span, ...]


class StdLogger(LoggerWrapper):
    def __init__(
        self,
        logger: NativeLogger,
        context: InContext | None = None,
        spans: InSpans = (),
    ) -> None:
        self._wrapped = logger
        self._context = frozendict({} if context is None else context)
        self._spans = tuple(spans)

    def log(self, level, msg, context=None, **kwargs):
        numeric_level = level
        if not isinstance(numeric_level, int):
            numeric_level = logging.getLevelNamesMapping()[level.upper()]

        args = [numeric_level, msg]
        if context := {**self._context, **(context or {})}:
            args.append(context)

        extra = kwargs.pop("extra", {})
        assert RecordAttr.RAW_SPANS not in extra

        return self._wrapped.log(
            *args,
            extra={**extra, RecordAttr.RAW_SPANS: self._spans},
            **self._increment_stacklevel(kwargs),
        )

    @spanner_contextmanager
    def span(self, msg, context=None, /, sid=""):
        yield self
