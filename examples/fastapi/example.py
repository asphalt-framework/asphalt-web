from dataclasses import dataclass

from asphalt.core import Context
from fastapi import FastAPI

from asphalt.web.fastapi import AsphaltDepends, FastAPIComponent

application = FastAPI(debug=True)


@dataclass
class MyResource:
    """A dummy class representing a resource to be injected."""

    description: str


@application.get("/")
async def root(
    my_resource: MyResource = AsphaltDepends(),
    another_resource: MyResource = AsphaltDepends("another"),
):
    return {
        "message": "Hello World",
        "my resource": my_resource.description,
        "another resource": another_resource.description,
    }


class WebComponent(FastAPIComponent):
    async def start(self, ctx: Context):
        ctx.add_resource(MyResource("default resource"))
        ctx.add_resource(MyResource("another resource"), "another")
        return await super().start(ctx)
