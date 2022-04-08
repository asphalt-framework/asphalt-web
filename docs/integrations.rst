ASGI 3.0
========

Component: ``asgi``
Example: https://github.com/asphalt-framework/asphalt-web/tree/master/examples/asgi

This is a generic integration for ASGI applications.

Resources available to request handlers:

* the ASGI scope of the request (type: :class:`asgiref.typing.HTTPScope`, name: ``default``)

Django
======

Component: ``django``
Example: https://github.com/asphalt-framework/asphalt-web/tree/master/examples/django

This integration is based on the ASGI 3.0 integration.

Resources available to request handlers:

* the ASGI scope of the request (type: :class:`asgiref.typing.HTTPScope`, name: ``default``)
* the request object (type: :class:`django.http.HttpRequest`, name: ``default``)

Starlette
=========

Component: ``starlette``
Example: https://github.com/asphalt-framework/asphalt-web/tree/master/examples/starlette

This integration is based on the ASGI 3.0 integration.

Resources available to request handlers:

* the ASGI scope of the request (type: :class:`asgiref.typing.HTTPScope`, name: ``default``)
* the request object (type: :class:`starlette.requests.Request`, name: ``default``)

FastAPI
=======

Component: ``fastapi``
Example: https://github.com/asphalt-framework/asphalt-web/tree/master/examples/fastapi

This integration is based on the ASGI 3.0 integration.

FastAPI has its own dependency injection system which means Asphalt resources must be injected a
bit differently in FastAPI endpoints. Instead of using :func:`~fastapi.Depends` as the default
value for a resource parameter you wish to inject, you need to use
:func:`~asphalt.web.fastapi.AsphaltDepends` instead. The machinery in
:class:`~asphalt.web.fastapi.FastAPIComponent` will handle the appropriate translation.

Resources available to request handlers:

* the ASGI scope of the request (type: :class:`asgiref.typing.HTTPScope`, name: ``default``)
* the request object (type: :class:`starlette.requests.Request`, name: ``default``)

AIOHTTP
=======

Component: ``aiohttp``
Example: https://github.com/asphalt-framework/asphalt-web/tree/master/examples/aiohttp

Unlike the other frameworks supported here, AIOHTTP is not based on the ASGI standard.

Resources available to request handlers:

* the request object (type: :class:`aiohttp.web_request.Request`, name: ``default``)
