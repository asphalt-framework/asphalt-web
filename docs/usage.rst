Integrating web frameworks with Asphalt
=======================================

.. highlight:: bash

This library exists to enable easy integration of various web frameworks with Asphalt.
To do this, the web application must be run as part of an Asphalt application.

There are two fundamental approaches to integrating web frameworks with Asphalt:

#. Pass a ready-made application object (usually with the routes defined already) to the
   framework-specific component provided here
#. Let the framework-specific component create the application object, and inject it
   into subcomponents as a resource, and add routes dynamically there (not possible with
   the ``asgi`` and ``django`` components)

Practical examples
------------------

The two different methods are demonstrated in the following examples.

In ``static.py``, an application object is made and then handler for the root path is
added to it. Then it gets picked up by the framework specific component.

In ``dynamic.py``, a component gets declared instead. This component gets the
application injected into its ``start()`` method, where the handler for the root path is
installed to the application.

Django is an exception to this, as it requires a specific project structure. For Django,
its ``views.py`` module is presented here. The complete example can be found in the
:github:`repository <examples/django>`.

.. tabs::

   .. tab:: ASGI 3.0

      .. tabs::

         .. tab:: static.py

            .. include:: ../examples/asgi/static.py
               :code: python3

         .. tab:: config.yaml

            .. include:: ../examples/asgi/config.yaml
               :code: yaml

   .. tab:: FastAPI

      .. tabs::

         .. tab:: static.py

            .. include:: ../examples/fastapi/static.py
               :code: python3

         .. tab:: dynamic.py

            .. include:: ../examples/fastapi/dynamic.py
               :code: python3

         .. tab:: config.yaml

            .. include:: ../examples/fastapi/config.yaml
               :code: yaml

   .. tab:: Starlette

      .. tabs::

         .. tab:: static.py

            .. include:: ../examples/starlette/static.py
               :code: python3

         .. tab:: dynamic.py

            .. include:: ../examples/starlette/dynamic.py
               :code: python3

         .. tab:: config.yaml

            .. include:: ../examples/starlette/config.yaml
               :code: yaml

   .. tab:: Django

      .. tabs::

         .. tab:: views.py

            .. include:: ../examples/django/django_example/views.py
               :code: python3

         .. tab:: config.yaml

            .. include:: ../examples/django/config.yaml
               :code: yaml

   .. tab:: aiohttp

      .. tabs::

         .. tab:: static.py

            .. include:: ../examples/aiohttp/static.py
               :code: python3

         .. tab:: dynamic.py

            .. include:: ../examples/aiohttp/dynamic.py
               :code: python3

         .. tab:: config.yaml

            .. include:: ../examples/aiohttp/config.yaml
               :code: yaml

To run these examples, copy all files to the same directory, and then (assuming
``asphalt-web`` and the appropriate web framework itself are installed)::

    PYTHONPATH=. asphalt run config.yaml --service static

or, for the ``dynamic`` alternative (where available)::

    PYTHONPATH=. asphalt run config.yaml --service dynamic

Injecting resources to handler functions
----------------------------------------

In most cases, dependency injection works the same with request handler functions: you
decorate the function with ``@inject`` and add one or more type annotated arguments with
``resource()`` as the default. One framework – FastAPI – requires special measures,
however. This is due to FastAPI having its own dependency injection scheme which clashes
with Asphalt's. To make the two frameworks play well together, one needs to use
:func:`~asphalt.web.fastapi.AsphaltDepends` instead of
:func:`~fastapi.param_functions.Depends` for injecting Asphalt resources. Beyond that,
things should work the same. And of course you can have both FastAPI and Asphalt
dependencies in the same handler function.
