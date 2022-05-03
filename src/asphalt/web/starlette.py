from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from asgiref.typing import ASGI3Application, HTTPScope, WebSocketScope
from asphalt.core import Context, current_context
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Receive, Scope, Send

from asphalt.web.asgi3 import ASGIComponent


class AsphaltMiddleware(BaseHTTPMiddleware):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async with Context() as ctx:
            if scope["type"] == "http":
                ctx.add_resource(scope, types=[HTTPScope])
            elif scope["type"] == "websocket":
                ctx.add_resource(scope, types=[WebSocketScope])

            await super().__call__(scope, receive, send)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        current_context().add_resource(request)
        return await call_next(request)


class StarletteComponent(ASGIComponent[Starlette]):
    """
    A component that serves a Starlette application.

    :param app: the Starlette application object
    :param host: the IP address to bind to
    :param port: the port to bind to
    :param debug: whether to enable debug mode in an implicitly created application
        (default: the value of
        `__debug__ <https://docs.python.org/3/library/constants.html#debug__>`_;
        ignored if an application object is explicitly passed in)
    :param middlewares: list of callables or dicts to be added as middleware using
        :meth:`add_middleware`
    """

    def __init__(
        self,
        components: dict[str, dict[str, Any] | None] = None,
        *,
        app: Starlette | None = None,
        host: str = "127.0.0.1",
        port: int = 8000,
        debug: bool | None = None,
        middlewares: Sequence[Callable[..., ASGI3Application] | dict[str, Any]] = (),
    ) -> None:
        debug = debug if isinstance(debug, bool) else __debug__
        super().__init__(
            components,
            app=app or Starlette(debug=debug),
            host=host,
            port=port,
            middlewares=middlewares,
        )

    def setup_asphalt_middleware(self, app: Starlette) -> ASGI3Application:
        return AsphaltMiddleware(app)
