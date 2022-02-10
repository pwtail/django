
import inspect

#TODO threadlocal
import threading
import typing
from contextlib import contextmanager, asynccontextmanager

from django.db import connection

IS_ASYNC = True

def is_async():
    return IS_ASYNC


class Branch:
    def __init__(self):
        self.ns = {}

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        type = 'async' if is_async() else 'sync'
        func = self.ns[type, self.name]
        return func.__get__(instance)

    def __call__(self, func):
        name = func.__name__
        if inspect.iscoroutinefunction(func):
            type = 'async'
        else:
            type = 'sync'
        self.ns[type, name] = func
        return self



class RetCursor(typing.NamedTuple):
    rowcount: int

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def close(self):
        pass


def later(fn):
    assert not inspect.iscoroutinefunction(fn)
    sig = inspect.signature(fn)
    awaitables = [(k, v.default) for k, v in sig.parameters.items() if isinstance(v.default, typing.Awaitable)]

    async def awrapper(*args, **kwargs):
        for key, val in awaitables:
            kwargs[key] = await val
        val = fn(*args, **kwargs)
        if isinstance(val, typing.Awaitable):
            val = await val
        return val

    def wrapper(*args, **kwargs):
        if not is_async():
            return fn(*args, **kwargs)

        return awrapper(*args, **kwargs)

    return wrapper

wait = then = later

def value(val):
    @wait
    def f():
        return val
    return f()

wait.value = value
del value


def gen(fn):
    async def awrapper(*args, **kw):
        g = fn(*args, **kw)
        result = None
        while True:
            try:
                result = (await g.send(result))
            except StopIteration as ex:
                return ex.value

    def wrapper(*args, **kw):
        if is_async():
            return awrapper(*args, **kw)
        g = fn(*args, **kw)
        result = None
        while True:
            try:
                result = g.send(result)
            except StopIteration as ex:
                return ex.value

    return wrapper


@contextmanager
def zeroctx():
    yield




threadlocal = threading.local()


def set_connection(connection):
    threadlocal.connection = connection


#TODO using
def get_connection():
    return getattr(threadlocal, 'connection', None)
