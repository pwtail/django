
import inspect

#TODO threadlocal
import typing

IS_ASYNC = True

class Branch:
    def __init__(self):
        self.ns = {}

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        type = 'async' if IS_ASYNC else 'sync'
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
