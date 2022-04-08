from dataclasses import dataclass

from asphalt.core import Context

from asphalt.web.django import DjangoComponent


@dataclass
class MyResource:
    """A dummy class representing a resource to be injected."""

    description: str


class WebComponent(DjangoComponent):
    async def start(self, ctx: Context):
        ctx.add_resource(MyResource("default resource"))
        ctx.add_resource(MyResource("another resource"), "another")
        return await super().start(ctx)
