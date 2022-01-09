from __future__ import annotations
import asyncio
import typing
from functools import wraps, cached_property

if typing.TYPE_CHECKING:
    from django.db.models import QuerySet


class DeferredCall(typing.NamedTuple):
    func: object
    args: tuple
    kwargs: dict


class SyncDriver:
    def execute(self, deferred_calls):
        result = None
        while True:
            try:
                op = deferred_calls.send(result)
            except StopIteration as ex:
                return ex.value
            assert isinstance(op, tuple)
            func, args = op[0], op[1]
            assert callable(func)
            kwargs = None
            if isinstance(args, dict):
                kwargs = args
                args = ()
            elif len(op) > 2:
                kwargs = op[3]
            elif kwargs is None:
                kwargs = {}
            result = func(*args, **kwargs)


sync_driver = SyncDriver()

class AsyncDriver:

    async def execute(self, deferred_calls):
        result = None
        while True:
            try:
                op = deferred_calls.send(result)
            except StopIteration as ex:
                return ex.value
            assert isinstance(op, tuple)
            func, args = op[0], op[1]
            assert callable(func)
            kwargs = None
            if isinstance(args, dict):
                kwargs = args
                args = ()
            elif len(op) > 2:
                kwargs = op[3]
            elif kwargs is None:
                kwargs = {}
            result = await func(*args, **kwargs)


async_driver = AsyncDriver()

IS_ASYNC = True


def use_driver(func):
    def wrapper(*args, **kwargs):
        deferred_calls = func(*args, **kwargs)
        if not IS_ASYNC:
            driver = sync_driver
        else:
            driver = async_driver
        return driver.execute(deferred_calls)

    return wrapper

