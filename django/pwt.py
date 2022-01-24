from __future__ import annotations
import asyncio
import typing
from contextlib import contextmanager, asynccontextmanager
from functools import wraps, cached_property

if typing.TYPE_CHECKING:
    from django.db.models import QuerySet


class DeferredCall(typing.NamedTuple):
    func: object
    args: tuple
    kwargs: dict


#TODO
class Si:
    def execute(self, g):
        result = None
        while 1:
            result = g.send(result)


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

#TODO G_func = unwrapped(func)

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


#TODO tofunc
def use_driver(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        deferred_calls = func(*args, **kwargs)
        if not IS_ASYNC:
            driver = sync_driver
        else:
            driver = async_driver
        return driver.execute(deferred_calls)

    wrapper.wraps = func
    return wrapper



class RetCursor(typing.NamedTuple):
    rowcount: int

    def close(self):
        pass
