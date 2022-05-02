import json

import pytest
import websockets
from aiohttp.abc import Request
from aiohttp.web_middlewares import middleware
from asphalt.core import Component, Context, inject, require_resource, resource
from httpx import AsyncClient


@inject
async def root(
    request,
    my_resource: str = resource(),
    another_resource: str = resource("another"),
):
    from aiohttp.web_response import json_response

    return json_response(
        {
            "message": request.query["param"],
            "my resource": my_resource,
            "another resource": another_resource,
        }
    )


@inject
async def ws_root(
    request,
    my_resource: str = resource(),
    another_resource: str = resource("another"),
):
    from aiohttp.web_ws import WebSocketResponse

    ws = WebSocketResponse()
    await ws.prepare(request)
    message = await ws.receive_str()
    await ws.send_json(
        {
            "message": f"Hello {message}",
            "my resource": my_resource,
            "another resource": another_resource,
        }
    )


class RouteComponent(Component):
    async def start(self, ctx: Context) -> None:
        from aiohttp.web_app import Application

        app = require_resource(Application)
        app.router.add_route("GET", "/", root)


def setup_text_replacer(app, *, text: str, replacement: str) -> None:
    @middleware
    async def text_replacer(request: Request, handler) -> None:
        response = await handler(request)
        response.text = response.text.replace(text, replacement)
        return response

    app.middlewares.append(text_replacer)


@pytest.mark.parametrize("method", ["static", "dynamic"])
@pytest.mark.asyncio
async def test_aiohttp_http(unused_tcp_port: int, method: str):
    pytest.importorskip("aiohttp", reason="aiohttp not available")

    from aiohttp.web_app import Application
    from aiohttp.web_routedef import RouteTableDef

    from asphalt.web.aiohttp import AIOHTTPComponent

    application = Application()
    if method == "static":
        routes = RouteTableDef()
        routes.get("/")(root)
        application.add_routes(routes)
        components = {}
    else:
        components = {"myroutes": {"type": RouteComponent}}

    async with Context() as ctx, AsyncClient() as http:
        ctx.add_resource("foo")
        ctx.add_resource("bar", name="another")
        await AIOHTTPComponent(
            components=components, app=application, port=unused_tcp_port
        ).start(ctx)

        # Ensure that the application got added as a resource
        ctx.require_resource(Application)

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
async def test_aiohttp_ws(unused_tcp_port: int):
    pytest.importorskip("aiohttp", reason="aiohttp not available")

    from aiohttp.web_app import Application
    from aiohttp.web_routedef import RouteTableDef

    from asphalt.web.aiohttp import AIOHTTPComponent

    routes = RouteTableDef()
    routes.get("/")(ws_root)
    application = Application()
    application.add_routes(routes)
    async with Context() as ctx:
        ctx.add_resource("foo")
        ctx.add_resource("bar", name="another")
        await AIOHTTPComponent(app=application, port=unused_tcp_port).start(ctx)

        # Ensure that the application got added as a resource
        ctx.require_resource(Application)

        async with websockets.connect(f"ws://localhost:{unused_tcp_port}") as ws:
            await ws.send("World")
            response = json.loads(await ws.recv())
            assert response == {
                "message": "Hello World",
                "my resource": "foo",
                "another resource": "bar",
            }


@pytest.mark.parametrize("method", ["direct", "dict"])
@pytest.mark.asyncio
async def test_aiohttp_middleware(unused_tcp_port: int, method: str):
    pytest.importorskip("aiohttp", reason="aiohttp not available")

    from aiohttp.web_app import Application

    from asphalt.web.aiohttp import AIOHTTPComponent

    application = Application()
    application.router.add_route("GET", "/", root)

    @middleware
    async def text_replacer(request: Request, handler) -> None:
        response = await handler(request)
        response.text = response.text.replace("Hello World", "Hello Middleware")
        return response

    if method == "direct":
        middlewares = [text_replacer]
    else:
        middlewares = [
            {
                "type": f"{__name__}:setup_text_replacer",
                "text": "Hello World",
                "replacement": "Hello Middleware",
            }
        ]

    async with Context() as ctx, AsyncClient() as http:
        ctx.add_resource("foo")
        ctx.add_resource("bar", name="another")
        await AIOHTTPComponent(
            app=application, port=unused_tcp_port, middlewares=middlewares
        ).start(ctx)

        # Ensure that the application got added as a resource
        ctx.require_resource(Application)

        response = await http.get(
            f"http://127.0.0.1:{unused_tcp_port}", params={"param": "Hello World"}
        )
        response.raise_for_status()
        assert response.json() == {
            "message": "Hello Middleware",
            "my resource": "foo",
            "another resource": "bar",
        }
