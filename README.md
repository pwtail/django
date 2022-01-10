 Vinyl, a django-based orm that is natively async
 ===========


[DEP-09](https://github.com/django/deps/blob/main/accepted/0009-async.rst) (Async django) states that making the orm natively async is out of the scope and should be a matter of further individual projects. *This* is such a project.

**Django-based async orm**


*Vinyl* is a django fork. However, it features no other big changes besides adding the async functionality. 

The sync mode remains first class, no adapters needed.

The fact that it is django-based means the API is stable and all tests from django can be reused.

**How it works. Approach #1: yield from**

I have found recently a more or less universal way to make a library usable in both sync and async contexts. It is done by using generators and `yield from`.
Let me demonstrate it on a simple example. Suppose we have a `SQLCompiler` class as shown below.

```python

class SQLCompiler:

    def execute_sql(self):
        ...
    
    if IS_ASYNC:
        async def execute_sql(self):
            ...
```

`.execute_sql()` is a method that makes a query to the database. It is sync or async depending on a global constant (the environment).
Here is how we can use it:

```python
class Query:
    
    @use_driver
    def fetch(self):
        ...
        yield from self.evaluate_main_query()

    def evaluate_main_query(self):
        yield from self.hit_the_db()

    def hit_the_db(self):
        ...
        yield compiler.execute_sql, ()

```

Look at the `hit_the_db` function. It yields a tuple: `(function, args, kwargs)`. That is a call that will be made. The function should be synchronous in the case of synchronous service and asynchronous otherwise.

The `@use_driver` decorator means that a specific database driver (sync or async) will be used to execute it, turning a generator into a function.

As a result, `Query.fetch` will be a regular function or will return a coroutine, depending on the `IS_ASYNC` constant (just like `execute_sql`).

**Other tricks**

The approach above works fine and without issues - at least until you actually need lazy operations and long-living generators in your code (yes, I'm aware of `QuerySet.iterator()` function and it is does not present a big challenge).

But one thing that I've learned that makes me optimistic about this project - is that very often that aproach is an overkill and a more simple way exists.

For example, as you know, querysets in django are lazy and their execution is delayed until the last moment. So it can actually hit the database in the `QuerySet.__await__` method which turned out to be not hard to implement (I am speaking about the [proof-of-concept](https://github.com/pwtail/django/pull/1/files) code here). Dealing with methods that don't return `QuerySet`, like `.get()` or `.aggregate()`, wasn't hard either.

Other example is the `prefetch_related` function where I gladly applied the `yield from` approach. Same as for the most of write operations like `Model.save()`

**API and semantics are preserved**

It is said in DEP-09 that there is no easy way to preserve the API and the semantics of django in the async usecase. While in my opinion it is all very doable.

For example, lets take one of the hardest parts: lazy attributes. Accessing an attribute of an object is a synchronous operation in python. That means you cannot do async db queries there and it might seem that you cannot implement them. However, the return value can be an awaitable. So here is an example of how they can be implemented: if the attribute wasn't prefetched before, we return an awaitable.

```python
>>> obj.related_obj
NotFetched()

>>> await _
<M: M object (5)>
```

Awaiting on the prefetched instances should probably result in an error. The same goes for queries like `obj.related.all()`: if present in cache, return, if not - should be awaited.

In most other cases it's pretty clear what the async API should be. So probably less documentation to write.


**Why a separate project?**

This indeed could be an enhancement to the django project itself, given that some agreement is reached with the django project. However, that would require the new version to be fully compatible, with all tests passing, before it could see light.

But here's a thing: the reason that people could find this project interesting is its async functionality, of course. The one that doesn't have any counterpart in django and therefore doesn't have to be compatible with anything. So first versions of vinyl can be released and be used in async services much sooner.

The sync version of vinyl - yes, it will be fully compatible with django. But it has less value since people can already use django for the same purposes.

So the plan is as follows: the first released version of vinyl will be intended solely for async services. The sync version will be available but won't be recommended for production. If the async version will be successful, there is no doubt, in my opinion, that vinyl will replace django some time. Because it provides both sync and async versions at the same time.

**The first version**

The first version is likely to be out pretty soon with just one database backend available (the [psycopg3](https://www.psycopg.org/psycopg3/docs/) driver, probably) and will be intended for async services. Will not break your code since you clearly don't have any code that is using it :)

Btw, it will be the first natively asynchronous python orm.
