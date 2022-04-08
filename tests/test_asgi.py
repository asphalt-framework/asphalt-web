import json
from urllib.parse import parse_qs

import pytest
from asgiref.typing import HTTPScope, ASGIReceiveCallable, ASGISendCallable
from httpx import AsyncClient

from asphalt.core import Context, Dependency, inject
from asphalt.web.asgi import ASGIComponent


@inject
async def application(
    scope: HTTPScope,
    receive: ASGIReceiveCallable,
    send: ASGISendCallable,
    my_resource: str = Dependency(),
    another_resource: str = Dependency("another"),
):
    assert scope["type"] == "http"
    query = parse_qs(scope["query_string"])
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


@pytest.mark.asyncio
async def test_asgi(unused_tcp_port: int):
    async with Context() as ctx, AsyncClient() as http:
        ctx.add_resource("foo")
        ctx.add_resource("bar", name="another")
        await ASGIComponent(app=application, port=unused_tcp_port).start(ctx)
        response = await http.get(f"http://127.0.0.1:{unused_tcp_port}",
                                  params={"param": "Hello World"})
        response.raise_for_status()
        assert response.json() == {
            "message": "Hello World",
            "my resource": "foo",
            "another resource": "bar",
        }
