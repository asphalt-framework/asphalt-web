import json

import pytest
import websockets
from asgiref.typing import HTTPScope, WebSocketScope
from asphalt.core import Context, current_context, inject, resource
from httpx import AsyncClient
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket

from asphalt.web.starlette import StarletteComponent


@inject
async def root(
    request: Request,
    my_resource: str = resource(),
    another_resource: str = resource("another"),
) -> Response:
    current_context().require_resource(HTTPScope)
    current_context().require_resource(Request)
    return JSONResponse(
        {
            "message": request.query_params["param"],
            "my resource": my_resource,
            "another resource": another_resource,
        }
    )


@inject
async def ws_root(
    websocket: WebSocket,
    my_resource: str = resource(),
    another_resource: str = resource("another"),
):
    current_context().require_resource(WebSocketScope)
    await websocket.accept()
    message = await websocket.receive_text()
    await websocket.send_json(
        {
            "message": f"Hello {message}",
            "my resource": my_resource,
            "another resource": another_resource,
        }
    )


application = Starlette(
    debug=True,
    routes=[
        Route("/", root),
        WebSocketRoute("/ws", ws_root),
    ],
)


@pytest.mark.asyncio
async def test_starlette_http(unused_tcp_port: int):
    async with Context() as ctx, AsyncClient() as http:
        ctx.add_resource("foo")
        ctx.add_resource("bar", name="another")
        await StarletteComponent(app=application, port=unused_tcp_port).start(ctx)
        response = await http.get(
            f"http://127.0.0.1:{unused_tcp_port}", params={"param": "Hello World"}
        )
        response.raise_for_status()
        assert response.json() == {
            "message": "Hello World",
            "my resource": "foo",
            "another resource": "bar",
        }


@pytest.mark.asyncio
async def test_starlette_ws(unused_tcp_port: int):
    async with Context() as ctx:
        ctx.add_resource("foo")
        ctx.add_resource("bar", name="another")
        await StarletteComponent(app=application, port=unused_tcp_port).start(ctx)
        async with websockets.connect(f"ws://localhost:{unused_tcp_port}/ws") as ws:
            await ws.send("World")
            response = json.loads(await ws.recv())
            assert response == {
                "message": "Hello World",
                "my resource": "foo",
                "another resource": "bar",
            }
