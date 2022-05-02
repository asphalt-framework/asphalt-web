import json
from dataclasses import dataclass

from asphalt.core import Context, inject, resource

from asphalt.web.asgi import ASGIComponent


@dataclass
class MyResource:
    """A dummy class representing a resource to be injected."""

    description: str


@inject
async def application(
    scope,
    receive,
    send,
    my_resource: MyResource = resource(),
    another_resource: MyResource = resource("another"),
):
    """Trivial example of a raw ASGI application without a framework."""
    if scope["type"] == "http":
        await receive()
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    [b"content-type", b"application/json"],
                ],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": json.dumps(
                    {
                        "message": "Hello World",
                        "my resource": my_resource.description,
                        "another resource": another_resource.description,
                    }
                ).encode(),
                "more_body": False,
            }
        )


class WebComponent(ASGIComponent):
    async def start(self, ctx: Context):
        ctx.add_resource(MyResource("default resource"))
        ctx.add_resource(MyResource("another resource"), "another")
        await super().start(ctx)
