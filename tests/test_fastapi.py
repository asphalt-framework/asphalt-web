import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from asphalt.core import Context
from asphalt.web.fastapi import AsphaltDepends, FastAPIComponent

application = FastAPI()


@application.get("/")
async def root(
    request: Request,
    my_resource: str = AsphaltDepends(),
    another_resource: str = AsphaltDepends("another"),
) -> Response:
    return JSONResponse(
        {
            "message": request.query_params["param"],
            "my resource": my_resource,
            "another resource": another_resource,
        }
    )


@pytest.mark.asyncio
async def test_fastapi(unused_tcp_port: int):
    async with Context() as ctx, AsyncClient() as http:
        ctx.add_resource("foo")
        ctx.add_resource("bar", name="another")
        await FastAPIComponent(app=application, port=unused_tcp_port).start(ctx)
        response = await http.get(f"http://127.0.0.1:{unused_tcp_port}",
                                  params={"param": "Hello World"})
        response.raise_for_status()
        assert response.json() == {
            "message": "Hello World",
            "my resource": "foo",
            "another resource": "bar",
        }
