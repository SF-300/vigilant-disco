import asyncio as aio
import typing as t


def iife[R](func: t.Callable[..., R]) -> R:
    return func()


def future_from_qt_signal(signal) -> aio.Future:
    """Convert a Qt signal to an asyncio future."""
    loop = aio.get_running_loop()
    future = loop.create_future()

    def slot(*args):
        signal.disconnect(slot)
        if not future.done():
            future.set_result(args[0] if args else None)

    signal.connect(slot)
    return future
