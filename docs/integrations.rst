Integrations
============

.. py:currentmodule:: asphalt.web

ASGI 3.0
--------

Component: ``asgi`` (:class:`.asgi.ASGIComponent`)

Example: https://github.com/asphalt-framework/asphalt-web/tree/master/examples/asgi

This is a generic integration for ASGI applications.

Resources available to request handlers:

* the ASGI scope of the request

  * type: `asgiref.typing.HTTPScope`_ or `asgiref.typing.WebSocketScope`_
  * name: ``default``

Django
------

Component: ``django`` (:class:`.django.DjangoComponent`)

Example: https://github.com/asphalt-framework/asphalt-web/tree/master/examples/django

This integration is based on the ASGI 3.0 integration.

Resources available to request handlers:

* the ASGI scope of the request

  * type: `asgiref.typing.HTTPScope`_
  * name: ``default``
* the request object

  * type: `django.http.HttpRequest`_
  * name: ``default``

.. note:: Websocket support via Django Channels has not been implemented.

Starlette
---------

Component: ``starlette`` (:class:`.starlette.StarletteComponent`)

Example: https://github.com/asphalt-framework/asphalt-web/tree/master/examples/starlette

This integration is based on the ASGI 3.0 integration.

Resources available to HTTP request handlers:

* the ASGI scope of the request

  * type: `asgiref.typing.HTTPScope`_
  * name: ``default``
* the request object

  * type: `starlette.requests.Request`_
  * name: ``default``

Resources available to websocket handlers:

* the ASGI scope of the request

  * type: `asgiref.typing.WebSocketScope`_
  * name: ``default``

FastAPI
-------

Component: ``fastapi`` (:class:`.fastapi.FastAPIComponent`)

Example: https://github.com/asphalt-framework/asphalt-web/tree/master/examples/fastapi

This integration is based on the ASGI 3.0 integration.

FastAPI has its own dependency injection system which means Asphalt resources must be
injected a bit differently in FastAPI endpoints. Instead of using
:func:`~fastapi.Depends` as the default value for a resource parameter you wish to
inject, you need to use :func:`~asphalt.web.fastapi.AsphaltDepends` instead. The
machinery in :class:`~asphalt.web.fastapi.FastAPIComponent` will handle the appropriate
translation.

Resources available to HTTP request handlers:

* the ASGI scope of the request

  * type: `asgiref.typing.HTTPScope`_
  * name: ``default``
* the request object

  * type: `starlette.requests.Request`_
  * name: ``default``

Resources available to websocket handlers:

* the ASGI scope of the request

  * type: `asgiref.typing.WebSocketScope`_
  * name: ``default``

AIOHTTP
-------

Component: ``aiohttp`` (:class:`.aiohttp.AIOHTTPComponent`)

Example: https://github.com/asphalt-framework/asphalt-web/tree/master/examples/aiohttp

Unlike the other frameworks supported here, AIOHTTP is not based on the ASGI standard.

Resources available to request handlers:

* the request object

  * type: `aiohttp.web_request.Request`_
  * name: ``default``

.. _asgiref.typing.HTTPScope: https://asgi.readthedocs.io/en/latest/specs/www.html#http-connection-scope
.. _asgiref.typing.WebSocketScope: https://asgi.readthedocs.io/en/latest/specs/www.html#websocket-connection-scope
.. _starlette.requests.Request: https://www.starlette.io/requests/
.. _django.http.HttpRequest: https://docs.djangoproject.com/en/3.2/ref/request-response/#httprequest-objects
.. _aiohttp.web_request.Request: https://docs.aiohttp.org/en/stable/web_reference.html#aiohttp.web.Request
