from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from inspect import Parameter, Signature, signature
from typing import Any

from asgiref.typing import ASGI3Application
from asphalt.core import require_resource
from fastapi import Depends, FastAPI
from fastapi.routing import APIRoute, APIWebSocketRoute

from .asgi3 import ASGIComponent
from .starlette import AsphaltMiddleware


@dataclass
class _AsphaltDependency:
    name: str
    cls: type = field(init=False)

    async def __call__(self):
        return require_resource(self.cls, self.name)

    def __hash__(self):
        return hash((self.name, self.cls))

    def __eq__(self, other):
        if isinstance(other, _AsphaltDependency):
            return self.name == other.name and self.cls is other.cls

        return NotImplemented


def AsphaltDepends(name: str = "default") -> Any:
    """
    Asphalt's version of FastAPI's :func:`~fastapi.Depends`.

    This should be marked as the default value on a parameter that should receive an
    Asphalt resource.

    :param name: the name of the resource within its unique type (default: ``default``)

    """
    return Depends(_AsphaltDependency(name))


class FastAPIComponent(ASGIComponent[FastAPI]):
    """
    A component that serves a FastAPI application.

    :param app: the FastAPI application object, or a module:varname reference to one
    :param host: the IP address to bind to
    :param port: the port to bind to
    :param debug: whether to enable debug mode in an implicitly created application
        (default: the value of
        `__debug__ <https://docs.python.org/3/library/constants.html#debug__>`_;
        ignored if an application object is explicitly passed in)
    :param middlewares: list of callables or dicts to be added as middleware using
        :meth:`add_middleware`
    """

    def __init__(
        self,
        components: dict[str, dict[str, Any] | None] = None,
        *,
        app: FastAPI | str | None = None,
        host: str = "127.0.0.1",
        port: int = 8000,
        debug: bool | None = None,
        middlewares: Sequence[Callable[..., ASGI3Application] | dict[str, Any]] = (),
    ) -> None:
        debug = debug if isinstance(debug, bool) else __debug__
        super().__init__(
            components,
            app=app or FastAPI(debug=debug),
            host=host,
            port=port,
            middlewares=middlewares,
        )

    def setup_asphalt_middleware(self, app: FastAPI) -> ASGI3Application:
        # Convert Asphalt dependencies into FastAPI dependencies
        for route in app.router.routes:
            if isinstance(route, (APIRoute, APIWebSocketRoute)):
                sig: Signature | None = None
                for dependency in route.dependant.dependencies:
                    if isinstance(dependency.call, _AsphaltDependency):
                        if sig is None:
                            sig = signature(route.endpoint)

                        annotation = sig.parameters[dependency.name].annotation
                        if annotation is Parameter.empty:
                            raise TypeError(
                                f"Dependency {dependency.name} in endpoint "
                                f"{route.path} is missing a type annotation"
                            )

                        dependency.call.cls = annotation

        return AsphaltMiddleware(app)
