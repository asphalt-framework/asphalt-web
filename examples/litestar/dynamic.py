from asphalt.core import Component, Context, require_resource
from litestar import Litestar, get


@get("/")
async def root() -> str:
    return "Hello, world!"


class WebRootComponent(Component):
    async def start(self, ctx: Context) -> None:
        require_resource(Litestar).register(root)
