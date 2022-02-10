
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



# def use_cursor(fn):
#     async def awrapper(*args, **kwargs):
#         async with cursor():
#             return await fn(*args, cursor=cursor, **kwargs)
#
#     def wrapper(*args, **kwargs):
#         if not is_async():
#             with cursor():
#                 return fn(*args, cursor=cursor, **kwargs)
#         return awrapper(*args, **kwargs)
#
#     return wrapper



threadlocal = threading.local()

def set_connection(connection):
    threadlocal.connection = connection

#TODO using
def get_connection():
    return getattr(threadlocal, 'connection', None)

# async def te():
#     po = await connection.start_pool()
#     async with po.connection() as conn:
#         # async with conn.transaction():
#         async with conn.cursor() as cur:
#             await cur.execute('select 1')
#             v = await cur.fetchall()
#         print(v)
#
# async def te2():
#     import psycopg
#     async with await psycopg.AsyncConnection.connect("dbname=smog user=postgres password=postgre") as aconn:
#         async with aconn.cursor() as cur:
#             await cur.execute('select 1')
#             v = await cur.fetchall()
#     print(v)
