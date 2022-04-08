import pytest

pytest.importorskip('aiohttp', reason='aiohttp not available')

from aiohttp.abc import Request
from aiohttp.web_app import Application
from aiohttp.web_response import json_response, Response
from aiohttp.web_routedef import RouteTableDef
from httpx import AsyncClient

from asphalt.core import Context, inject, Dependency
from asphalt.web.aiohttp import AIOHTTPComponent

routes = RouteTableDef()


@routes.get("/")
@inject
async def root(
    request: Request,
    my_resource: str = Dependency(),
    another_resource: str = Dependency("another"),
) -> Response:
    return json_response(
        {
            "message": request.query["param"],
            "my resource": my_resource,
            "another resource": another_resource,
        }
    )


@pytest.mark.asyncio
async def test_aiohttp(unused_tcp_port: int):
    application = Application()
    application.add_routes(routes)
    async with Context() as ctx, AsyncClient() as http:
        ctx.add_resource("foo")
        ctx.add_resource("bar", name="another")
        await AIOHTTPComponent(app=application, site={'port': unused_tcp_port}).start(ctx)
        response = await http.get(f"http://127.0.0.1:{unused_tcp_port}",
                                  params={"param": "Hello World"})
        response.raise_for_status()
        assert response.json() == {
            "message": "Hello World",
            "my resource": "foo",
            "another resource": "bar",
        }