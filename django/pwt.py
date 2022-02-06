
import inspect

#TODO threadlocal
import typing

IS_ASYNC = False

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

    def close(self):
        pass


def wait(fn):
    assert not inspect.iscoroutinefunction(fn)
    sig = inspect.signature(fn)
    kwargs = {k: v.default for k, v in sig.parameters.items()}
    if not is_async():
        return lambda: fn(**kwargs)

    async def wrapper():
        for key, value in tuple(kwargs.items()):
            kwargs[key] = await value
        return fn(**kwargs)
    return wrapper

def value(val):
    @wait
    def f():
        return val
    return f()

wait.value = value
del value
