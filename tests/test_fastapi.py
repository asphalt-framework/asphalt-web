import json

import pytest
import websockets
from asgiref.typing import ASGI3Application, HTTPScope, WebSocketScope
from asphalt.core import Component, Context, inject, require_resource, resource
from fastapi import FastAPI
from httpx import AsyncClient
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.websockets import WebSocket

from asphalt.web.fastapi import AsphaltDepends, FastAPIComponent


@pytest.mark.parametrize("method", ["static", "dynamic"])
@pytest.mark.asyncio
async def test_fastapi_http(unused_tcp_port: int, method: str):
    async def root(
        request: Request,
        my_resource: str = AsphaltDepends(),
        another_resource: str = AsphaltDepends("another"),
    ) -> Response:
        require_resource(HTTPScope)
        require_resource(Request)
        return JSONResponse(
            {
                "message": request.query_params["param"],
                "my resource": my_resource,
                "another resource": another_resource,
            }
        )

    application = FastAPI()
    if method == "static":
        application.add_api_route("/", root)
        components = {}
    else:

        class RouteComponent(Component):
            @inject
            async def start(self, ctx: Context, app: FastAPI = resource()) -> None:
                app.add_api_route("/", root)

        components = {"myroutes": {"type": RouteComponent}}

    async with Context() as ctx, AsyncClient() as http:
        ctx.add_resource("foo")
        ctx.add_resource("bar", name="another")
        await FastAPIComponent(
            components=components, app=application, port=unused_tcp_port
        ).start(ctx)

        # Ensure that the application got added as a resource
        asgi_app = ctx.require_resource(ASGI3Application)
        fastapi_app = ctx.require_resource(FastAPI)
        assert fastapi_app is asgi_app

        response = await http.get(
            f"http://127.0.0.1:{unused_tcp_port}", params={"param": "Hello World"}
        )
        response.raise_for_status()
        assert response.json() == {
            "message": "Hello World",
            "my resource": "foo",
            "another resource": "bar",
        }


@pytest.mark.parametrize("method", ["static", "dynamic"])
@pytest.mark.asyncio
async def test_fastapi_ws(unused_tcp_port: int, method: str):
    async def ws_root(
        websocket: WebSocket,
        my_resource: str = AsphaltDepends(),
        another_resource: str = AsphaltDepends("another"),
    ):
        require_resource(WebSocketScope)
        await websocket.accept()
        message = await websocket.receive_text()
        await websocket.send_json(
            {
                "message": f"Hello {message}",
                "my resource": my_resource,
                "another resource": another_resource,
            }
        )

    application = FastAPI()
    if method == "static":
        application.add_api_websocket_route("/ws", ws_root)
        components = {}
    else:

        class RouteComponent(Component):
            @inject
            async def start(self, ctx: Context, app: FastAPI = resource()) -> None:
                app.add_api_websocket_route("/ws", ws_root)

        components = {"myroutes": {"type": RouteComponent}}

    async with Context() as ctx:
        ctx.add_resource("foo")
        ctx.add_resource("bar", name="another")
        await FastAPIComponent(
            components=components, app=application, port=unused_tcp_port
        ).start(ctx)

        # Ensure that the application got added as a resource
        asgi_app = ctx.require_resource(ASGI3Application)
        fastapi_app = ctx.require_resource(FastAPI)
        assert fastapi_app is asgi_app

        async with websockets.connect(f"ws://localhost:{unused_tcp_port}/ws") as ws:
            await ws.send("World")
            response = json.loads(await ws.recv())
            assert response == {
                "message": "Hello World",
                "my resource": "foo",
                "another resource": "bar",
            }
