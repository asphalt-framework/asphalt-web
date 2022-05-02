from asphalt.core import Component, Context, inject, resource
from fastapi import FastAPI, Response


async def root() -> Response:
    return Response("Hello, world!")


class WebRootComponent(Component):
    @inject
    async def start(self, ctx: Context, app: FastAPI = resource()) -> None:
        app.add_api_route("/", root)
