import typing as t


def iife[R](func: t.Callable[..., R]) -> R:
    return func()
