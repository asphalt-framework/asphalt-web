import pytest
from asphalt.core import Context
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_asgi(unused_tcp_port: int):
    pytest.importorskip("django", reason="Django not available")

    from asphalt.web.django import DjangoComponent

    from .django_app.asgi import application

    async with Context() as ctx, AsyncClient() as http:
        ctx.add_resource("foo")
        ctx.add_resource("bar", name="another")
        await DjangoComponent(app=application, port=unused_tcp_port).start(ctx)
        response = await http.get(
            f"http://127.0.0.1:{unused_tcp_port}", params={"param": "Hello World"}
        )
        response.raise_for_status()
        assert response.json() == {
            "message": "Hello World",
            "my resource": "foo",
            "another resource": "bar",
        }