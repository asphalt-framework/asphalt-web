import pytest
from httpx import AsyncClient
from uvicorn import Server

from asphalt.core import Context, Dependency, inject
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from asphalt.web.starlette import StarletteComponent


@inject
async def root(
    request: Request,
    my_resource: str = Dependency(),
    another_resource: str = Dependency("another"),
) -> Response:
    return JSONResponse(
        {
            "message": request.query_params["param"],
            "my resource": my_resource,
            "another resource": another_resource,
        }
    )


application = Starlette(
    debug=True,
    routes=[
        Route("/", root),
    ],
)


@pytest.mark.asyncio
async def test_starlette(unused_tcp_port: int):
    async with Context() as ctx, AsyncClient() as http:
        ctx.add_resource("foo")
        ctx.add_resource("bar", name="another")
        await StarletteComponent(app=application, port=unused_tcp_port).start(ctx)
        response = await http.get(f"http://127.0.0.1:{unused_tcp_port}",
                                  params={"param": "Hello World"})
        response.raise_for_status()
        assert response.json() == {
            "message": "Hello World",
            "my resource": "foo",
            "another resource": "bar",
        }
