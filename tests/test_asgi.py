import json
from typing import cast
from urllib.parse import parse_qs

import pytest
import websockets
from asgiref.typing import (
    ASGIReceiveCallable,
    ASGISendCallable,
    HTTPScope,
    WebSocketScope,
)
from asphalt.core import Context, _Dependency, current_context, inject
from httpx import AsyncClient

from asphalt.web.asgi import ASGIComponent


@inject
async def application(
    scope: HTTPScope,
    receive: ASGIReceiveCallable,
    send: ASGISendCallable,
    my_resource: str = _Dependency(),
    another_resource: str = _Dependency("another"),
):
    if scope["type"] == "http":
        current_context().require_resource(HTTPScope)
        query = parse_qs(cast(bytes, scope["query_string"]))
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
                        "message": query[b"param"][0].decode(),
                        "my resource": my_resource,
                        "another resource": another_resource,
                    }
                ).encode(),
                "more_body": False,
            }
        )
    elif scope["type"] == "websocket":
        current_context().require_resource(WebSocketScope)
        await receive()  # Receive connection
        await send(  # Accept connection
            {
                "type": "websocket.accept",
            }
        )
        packet = await receive()
        await send(
            {
                "type": "websocket.send",
                "text": json.dumps(
                    {
                        "message": "Hello " + packet["text"],
                        "my resource": my_resource,
                        "another resource": another_resource,
                    }
                ),
            }
        )


@pytest.mark.asyncio
async def test_asgi_http(unused_tcp_port: int):
    async with Context() as ctx, AsyncClient() as http:
        ctx.add_resource("foo")
        ctx.add_resource("bar", name="another")
        await ASGIComponent(app=application, port=unused_tcp_port).start(ctx)
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
async def test_asgi_ws(unused_tcp_port: int):
    async with Context() as ctx:
        ctx.add_resource("foo")
        ctx.add_resource("bar", name="another")
        await ASGIComponent(app=application, port=unused_tcp_port).start(ctx)
        async with websockets.connect(f"ws://localhost:{unused_tcp_port}") as ws:
            await ws.send("World")
            response = json.loads(await ws.recv())
            assert response == {
                "message": "Hello World",
                "my resource": "foo",
                "another resource": "bar",
            }
