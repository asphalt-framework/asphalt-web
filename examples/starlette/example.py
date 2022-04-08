from dataclasses import dataclass

from asphalt.core import Context, Dependency, inject
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from asphalt.web.starlette import StarletteComponent


@dataclass
class MyResource:
    """A dummy class representing a resource to be injected."""

    description: str


@inject
async def root(
    request: Request,
    my_resource: MyResource = Dependency(),
    another_resource: MyResource = Dependency("another"),
) -> Response:
    return JSONResponse(
        {
            "message": "Hello World",
            "my resource": my_resource.description,
            "another resource": another_resource.description,
        }
    )


application = Starlette(
    debug=True,
    routes=[
        Route("/", root),
    ],
)


class WebComponent(StarletteComponent):
    async def start(self, ctx: Context):
        ctx.add_resource(MyResource("default resource"))
        ctx.add_resource(MyResource("another resource"), "another")
        return await super().start(ctx)
