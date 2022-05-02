from __future__ import annotations

from dataclasses import dataclass, field
from inspect import Parameter, Signature, signature
from typing import Any, TypeVar

from asgiref.typing import ASGI3Application
from asphalt.core import current_context
from fastapi import Depends, FastAPI
from fastapi.routing import APIRoute, APIWebSocketRoute

from .asgi import ASGIComponent
from .starlette import AsphaltMiddleware

T_ResourceType = TypeVar("T_ResourceType")


@dataclass
class _AsphaltDependency:
    name: str
    cls: type = field(init=False)

    async def __call__(self):
        return await current_context().request_resource(self.cls, self.name)

    def __hash__(self):
        return hash((self.name, self.cls))

    def __eq__(self, other):
        if isinstance(other, _AsphaltDependency):
            return self.name == other.name and self.cls is other.cls

        return NotImplemented


def AsphaltDepends(name: str = "default") -> Any:
    return Depends(_AsphaltDependency(name))


class FastAPIComponent(ASGIComponent[FastAPI]):
    def wrap_in_middleware(self, app: FastAPI) -> ASGI3Application:
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
