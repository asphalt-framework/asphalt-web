from __future__ import annotations

from asyncio import create_task, sleep
from dataclasses import dataclass
from inspect import isfunction
from typing import Any, Generic, TypeVar

import uvicorn
from asgiref.typing import (
    ASGI3Application,
    ASGIReceiveCallable,
    ASGISendCallable,
    HTTPScope,
    Scope,
    WebSocketScope,
)
from asphalt.core import (
    ContainerComponent,
    Context,
    context_teardown,
    resolve_reference,
)
from uvicorn import Config

T_Application = TypeVar("T_Application", bound=ASGI3Application)


@dataclass
class AsphaltMiddleware:
    """
    Generic ASGI middleware for Asphalt integration.

    This middleware wraps both HTTP requests and websocket connections in their own
    contexts and exposes the ASGI scope object as a resource.

    :param asgiref.typing.ASGI3Application app: the wrapped ASGI 3.0 application
    """

    app: ASGI3Application

    async def __call__(
        self, scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None:
        if scope["type"] in ("http", "websocket"):
            async with Context() as ctx:
                scope_type = HTTPScope if scope["type"] == "http" else WebSocketScope
                ctx.add_resource(scope, types=[scope_type])
                await self.app(scope, receive, send)
        else:
            await self.app(scope, receive, send)


class ASGIComponent(ContainerComponent, Generic[T_Application]):
    """
    A component that serves the given ASGI 3.0 application via Uvicorn.

    :param asgiref.typing.ASGI3Application app: the ASGI application to serve
    :param str host: the IP address to bind to
    :param int port: the port to bind to (default: 8000)
    """

    def __init__(
        self,
        components: dict[str, dict[str, Any] | None] = None,
        *,
        app: T_Application,
        host: str = "127.0.0.1",
        port: int = 8000,
    ) -> None:
        super().__init__(components)
        self.app: T_Application = resolve_reference(app)
        self.host = host
        self.port = port

    def wrap_in_middleware(self, app: T_Application) -> ASGI3Application:
        return AsphaltMiddleware(app)

    @context_teardown
    async def start(self, ctx: Context):
        config = Config(
            app=self.wrap_in_middleware(self.app),
            host=self.host,
            port=self.port,
            use_colors=False,
            log_config=None,
            lifespan="off",
        )

        types = [ASGI3Application]
        if not isfunction(self.app):
            types.append(type(self.app))

        ctx.add_resource(self.app, types=types)
        await super().start(ctx)

        server = uvicorn.Server(config)
        server.install_signal_handlers = lambda: None
        server_task = create_task(server.serve())
        while not server.started:
            await sleep(0)

        yield

        server.should_exit = True
        await server_task
