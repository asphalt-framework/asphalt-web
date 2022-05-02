from __future__ import annotations

from asgiref.typing import ASGI3Application, HTTPScope, WebSocketScope
from asphalt.core import Context, current_context
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Receive, Scope, Send

from asphalt.web.asgi import ASGIComponent


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

    :param starlette.applications.Starlette app: the Starlette application object
    """

    def wrap_in_middleware(self, app: Starlette) -> ASGI3Application:
        return AsphaltMiddleware(app)
