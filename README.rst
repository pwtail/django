**vinyl - a new orm for django**

Vinyl is a new orm based on django. Its unique feature is that it supports both sync and async mode (natively!).

It isn't 100% compatible with django (but is 99% compatible. And uses 99% of django code). But it is compatible with django models and settings, so imho some day it will replace the `django.db` package.

The unsupported bits of django API isn't something impossible to support, it most often is something very rarely used functionality that is difficult

Vinyl enables creating web applications that have both WSGI and ASGI endpoints. That is logically a single application and commonly using the same python environment. Of course it considers `sync_to_async` found in [`asgiref`](https://github.com/django/asgiref) a heresy and provides native asynchrony.
