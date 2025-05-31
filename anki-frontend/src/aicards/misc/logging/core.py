import asyncio as aio
import contextlib
import typing as t
import logging
import unittest.mock

from .base import LoggerLike, SpannerLike
from .utils import run_with_logger_substituted


class Spanner[V: LoggerLike = LoggerLike](SpannerLike[V]):
    def __init__(self, cm: t.ContextManager[V]) -> None:
        self._cm = cm

    def __enter__(self) -> V:
        result = self._cm.__enter__()
        return result

    def __exit__(self, *args, **kwargs) -> bool | None:
        return self._cm.__exit__(*args, **kwargs)

    @t.overload
    def __call__[**P, R](
        self,
        f: t.Callable[P, R],
        /,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R: ...

    @t.overload
    def __call__[**P, R](
        self,
        f: t.Callable[P, t.Coroutine[t.Any, R, t.Any]],
        /,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> t.Awaitable[R]: ...

    def __call__(self, f, /, *args, **kwargs):
        if not aio.iscoroutinefunction(f):
            with self._cm as logger:
                return run_with_logger_substituted(logger, f, *args, **kwargs)

        async def driver():
            # NOTE: As a precaution against stuff like "Eager Task Factory", yield control to event loop to ensure that
            #       we've been scheduled at least once, so that we run actual interesting code inside the
            #       already-copied contextvars.Context (if copying will take place at all).
            await aio.sleep(0)
            with self._cm as logger:
                return await run_with_logger_substituted(logger, f, *args, **kwargs)

        return driver()


def spanner_contextmanager[**PO, R: LoggerLike](
    func: t.Callable[PO, t.Iterator[R]],
) -> t.Callable[PO, SpannerLike[R]]:
    cm_func = contextlib.contextmanager(func)
    return lambda *args, **kwargs: Spanner(cm_func(*args, **kwargs))


class LoggerWrapper(LoggerLike):
    def __init__(self, wrapped: LoggerLike) -> None:
        self._wrapped = wrapped

    def log(self, *args, **kwargs) -> None:
        return self._wrapped.log(*args, **kwargs)

    def debug(self, *args, **kwargs):
        return self.log("debug", *args, **self._increment_stacklevel(kwargs))

    def info(self, *args, **kwargs):
        return self.log("info", *args, **self._increment_stacklevel(kwargs))

    def warn(self, *args, **kwargs):
        return self.log("warning", *args, **self._increment_stacklevel(kwargs))

    def error(self, *args, **kwargs):
        return self.log("error", *args, **self._increment_stacklevel(kwargs))

    def critical(self, *args, **kwargs):
        return self.log("critical", *args, **self._increment_stacklevel(kwargs))

    def span(self, *args, **kwargs) -> SpannerLike[t.Self]:
        return self._wrapped.span(*args, **kwargs)

    def _increment_stacklevel[T: t.MutableMapping](self, kwargs: T) -> T:
        stacklevel = kwargs.get("stacklevel", 1)
        assert isinstance(stacklevel, int)
        kwargs["stacklevel"] = stacklevel + 1
        return kwargs

    def __str__(self) -> str:
        return str(self._wrapped)


class _NullLogger(LoggerWrapper):
    def __init__(self) -> None:
        super().__init__(unittest.mock.Mock(spec=logging.Logger))

    @spanner_contextmanager
    def span(self, *args, **kwargs):
        yield self

    def __bool__(self):
        return False


null_logger = _NullLogger()
