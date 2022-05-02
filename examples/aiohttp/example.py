from dataclasses import dataclass

from aiohttp.abc import Request
from aiohttp.web_app import Application
from aiohttp.web_response import Response, json_response
from aiohttp.web_routedef import RouteTableDef
from asphalt.core import Context, inject, resource

from asphalt.web.aiohttp import AIOHTTPComponent

routes = RouteTableDef()


@dataclass
class MyResource:
    """A dummy class representing a resource to be injected."""

    description: str


@routes.get("/")
@inject
async def root(
    request: Request,
    my_resource: MyResource = resource(),
    another_resource: MyResource = resource("another"),
) -> Response:
    return json_response(
        {
            "message": "Hello World",
            "my resource": my_resource.description,
            "another resource": another_resource.description,
        }
    )


app = Application(debug=True)
app.add_routes(routes)


class WebComponent(AIOHTTPComponent):
    async def start(self, ctx: Context):
        ctx.add_resource(MyResource("default resource"))
        ctx.add_resource(MyResource("another resource"), "another")
        return await super().start(ctx)
